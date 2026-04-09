from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests


DEFAULT_TIMEOUT = 30


@dataclass
class SessionContext:
    base_url: str
    token: str
    tenant_id: str

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "X-Tenant-ID": self.tenant_id,
            "Content-Type": "application/json",
        }


class Recorder:
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.actions_path = run_dir / "actions.jsonl"
        self.errors_path = run_dir / "errors.jsonl"
        self.actions = 0
        self.errors = 0

    def action(self, kind: str, payload: dict[str, Any]) -> None:
        self.actions += 1
        self._append(self.actions_path, {"ts": _utc_now(), "kind": kind, **payload})

    def error(self, kind: str, payload: dict[str, Any]) -> None:
        self.errors += 1
        self._append(self.errors_path, {"ts": _utc_now(), "kind": kind, **payload})

    @staticmethod
    def _append(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _request(method: str, url: str, *, expected: tuple[int, ...] = (200,), recorder: Recorder | None = None, **kwargs: Any) -> requests.Response:
    response = requests.request(method, url, timeout=DEFAULT_TIMEOUT, **kwargs)
    if response.status_code not in expected:
        body_preview = response.text[:1000]
        if recorder is not None:
            recorder.error(
                "http_error",
                {
                    "method": method,
                    "url": url,
                    "status_code": response.status_code,
                    "response": body_preview,
                },
            )
        raise RuntimeError(f"{method} {url} failed with {response.status_code}: {body_preview}")
    return response


def signup_or_login(base_url: str, email: str, password: str, tenant_name: str, recorder: Recorder) -> SessionContext:
    signup_url = f"{base_url}/auth/signup"
    signup_payload = {"tenant_name": tenant_name, "email": email, "password": password}
    signup_resp = requests.post(signup_url, json=signup_payload, timeout=DEFAULT_TIMEOUT)
    if signup_resp.status_code == 200:
        body = signup_resp.json()
        recorder.action("auth.signup", {"email": email, "tenant_id": body["tenant_id"]})
        return SessionContext(base_url=base_url, token=body["token"], tenant_id=body["tenant_id"])

    recorder.action("auth.signup_skipped", {"status_code": signup_resp.status_code, "email": email})
    login_resp = _request(
        "POST",
        f"{base_url}/auth/login_email",
        json={"email": email, "password": password},
        expected=(200,),
        recorder=recorder,
    )
    body = login_resp.json()
    if body.get("mode") != "authenticated":
        raise RuntimeError(f"Unsupported login flow for simulator: {body}")
    auth = body["auth"]
    recorder.action("auth.login", {"email": email, "tenant_id": auth["tenant_id"]})
    return SessionContext(base_url=base_url, token=auth["token"], tenant_id=auth["tenant_id"])


def get_default_location(ctx: SessionContext, recorder: Recorder) -> str:
    response = _request("GET", f"{ctx.base_url}/crm/locations/default", headers=ctx.headers, recorder=recorder)
    location_id = response.json()["id"]
    recorder.action("location.default", {"location_id": location_id})
    return location_id


def create_service(ctx: SessionContext, idx: int, recorder: Recorder, rng: random.Random) -> str:
    payload = {
        "name": f"QA Service {idx}",
        "price_cents": rng.randint(3000, 15000),
        "duration_minutes": rng.choice([30, 45, 60, 90]),
    }
    response = _request("POST", f"{ctx.base_url}/crm/services", headers=ctx.headers, json=payload, recorder=recorder)
    service_id = response.json()["id"]
    recorder.action("service.create", {"service_id": service_id, "payload": payload})
    return service_id


def create_customer(ctx: SessionContext, idx: int, recorder: Recorder) -> str:
    payload = {
        "name": f"QA Customer {idx}",
        "phone": f"555{idx:06d}",
        "email": f"qa-customer-{idx}@example.com",
    }
    response = _request("POST", f"{ctx.base_url}/crm/customers", headers=ctx.headers, json=payload, recorder=recorder)
    customer_id = response.json()["id"]
    recorder.action("customer.create", {"customer_id": customer_id, "payload": payload})
    return customer_id


def create_appointment(
    ctx: SessionContext,
    *,
    customer_id: str,
    service_id: str,
    location_id: str,
    starts_at: datetime,
    ends_at: datetime,
    idx: int,
    recorder: Recorder,
) -> dict[str, Any]:
    payload = {
        "customer_id": customer_id,
        "service_id": service_id,
        "location_id": location_id,
        "starts_at": starts_at.isoformat().replace("+00:00", "Z"),
        "ends_at": ends_at.isoformat().replace("+00:00", "Z"),
        "status": "booked",
        "notes": f"simulated-appointment-{idx}",
    }
    response = _request("POST", f"{ctx.base_url}/crm/appointments", headers=ctx.headers, json=payload, expected=(200, 409), recorder=recorder)
    if response.status_code == 409:
        recorder.action("appointment.conflict", {"payload": payload, "response": response.json()})
        raise RuntimeError("appointment overlap encountered during creation")
    body = response.json()
    recorder.action("appointment.create", {"appointment_id": body["id"], "payload": payload})
    return body


def mutate_appointment(
    ctx: SessionContext,
    appointment_id: str,
    mutation: dict[str, Any],
    recorder: Recorder,
    *,
    label: str,
) -> dict[str, Any]:
    response = _request(
        "PATCH",
        f"{ctx.base_url}/crm/appointments/{appointment_id}",
        headers=ctx.headers,
        json=mutation,
        expected=(200, 409),
        recorder=recorder,
    )
    if response.status_code == 409:
        recorder.action("appointment.conflict", {"appointment_id": appointment_id, "mutation": mutation, "response": response.json()})
        raise RuntimeError(f"appointment overlap encountered during {label}")
    body = response.json()
    recorder.action(label, {"appointment_id": appointment_id, "mutation": mutation, "result": body})
    return body


def simulate(args: argparse.Namespace) -> int:
    base_url = args.base_url.rstrip("/")
    rng = random.Random(args.seed)

    run_id = args.run_id or f"opsim-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-seed{args.seed}"
    run_dir = Path("artifacts") / "operational-simulations" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    recorder = Recorder(run_dir)

    manifest = {
        "run_id": run_id,
        "base_url": base_url,
        "email": args.email,
        "tenant_name": args.tenant_name,
        "seed": args.seed,
        "customers": args.customers,
        "services": args.services,
        "appointments": args.appointments,
        "started_at": _utc_now(),
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    try:
        ctx = signup_or_login(base_url, args.email, args.password, args.tenant_name, recorder)
        location_id = get_default_location(ctx, recorder)

        service_ids = [create_service(ctx, idx, recorder, rng) for idx in range(args.services)]
        customer_ids = [create_customer(ctx, idx, recorder) for idx in range(args.customers)]

        created: list[dict[str, Any]] = []
        base = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
        for idx in range(args.appointments):
            slot = idx % 8
            day = idx // 8
            starts_at = base + timedelta(days=day, hours=slot)
            ends_at = starts_at + timedelta(minutes=60)
            customer_id = customer_ids[idx % len(customer_ids)]
            service_id = service_ids[idx % len(service_ids)]
            created.append(
                create_appointment(
                    ctx,
                    customer_id=customer_id,
                    service_id=service_id,
                    location_id=location_id,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    idx=idx,
                    recorder=recorder,
                )
            )

        summary = {
            "booked": 0,
            "completed": 0,
            "cancelled": 0,
            "no_show": 0,
            "rescheduled": 0,
        }

        for appointment in created:
            roll = rng.random()
            appointment_id = appointment["id"]
            if roll < 0.60:
                mutate_appointment(ctx, appointment_id, {"status": "completed"}, recorder, label="appointment.complete")
                summary["completed"] += 1
            elif roll < 0.75:
                mutate_appointment(
                    ctx,
                    appointment_id,
                    {"status": "cancelled", "cancelled_reason": "simulated_client_request"},
                    recorder,
                    label="appointment.cancel",
                )
                summary["cancelled"] += 1
            elif roll < 0.85:
                mutate_appointment(ctx, appointment_id, {"status": "no_show"}, recorder, label="appointment.no_show")
                summary["no_show"] += 1
            elif roll < 0.95:
                starts_at = datetime.fromisoformat(appointment["starts_at"].replace("Z", "+00:00")) + timedelta(days=1)
                ends_at = datetime.fromisoformat(appointment["ends_at"].replace("Z", "+00:00")) + timedelta(days=1)
                mutate_appointment(
                    ctx,
                    appointment_id,
                    {
                        "starts_at": starts_at.isoformat().replace("+00:00", "Z"),
                        "ends_at": ends_at.isoformat().replace("+00:00", "Z"),
                        "status": "booked",
                        "notes": "rescheduled-by-simulator",
                    },
                    recorder,
                    label="appointment.reschedule",
                )
                summary["rescheduled"] += 1
                summary["booked"] += 1
            else:
                recorder.action("appointment.keep_booked", {"appointment_id": appointment_id})
                summary["booked"] += 1

        output = {
            "run_id": run_id,
            "finished_at": _utc_now(),
            "seed": args.seed,
            "tenant_id": ctx.tenant_id,
            "total_actions": recorder.actions,
            "total_errors": recorder.errors,
            "status_summary": summary,
        }
        (run_dir / "summary.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(json.dumps(output, indent=2))
        return 0
    except Exception as exc:
        recorder.error("run.failed", {"message": str(exc)})
        summary = {
            "run_id": run_id,
            "finished_at": _utc_now(),
            "seed": args.seed,
            "failed": True,
            "error": str(exc),
            "total_actions": recorder.actions,
            "total_errors": recorder.errors,
        }
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2), file=sys.stderr)
        return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deterministic operational simulator for appointment lifecycle flows.")
    parser.add_argument("--base-url", required=True, help="Frontend base URL, for example https://your-frontend.onrender.com")
    parser.add_argument("--email", required=True, help="QA user email")
    parser.add_argument("--password", required=True, help="QA user password")
    parser.add_argument("--tenant-name", default="QA Salon", help="Tenant name used during signup")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--customers", type=int, default=20)
    parser.add_argument("--services", type=int, default=5)
    parser.add_argument("--appointments", type=int, default=100)
    parser.add_argument("--run-id", default=None, help="Optional explicit run id")
    return parser.parse_args()


def main() -> int:
    return simulate(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())

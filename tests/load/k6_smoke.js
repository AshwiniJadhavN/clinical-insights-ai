import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export const options = {
  vus: Number(__ENV.VUS || 5),
  duration: __ENV.DURATION || "20s",
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<800"],
  },
};

export default function () {
  const health = http.get(`${BASE_URL}/health`);
  const ready = http.get(`${BASE_URL}/health/ready`);

  check(health, {
    "GET /health status is 200": (r) => r.status === 200,
  });

  check(ready, {
    "GET /health/ready status is 200": (r) => r.status === 200,
  });

  sleep(0.2);
}

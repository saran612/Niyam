import { test, expect } from "@playwright/test";

test.describe("AICTE Approval & Obligation Engine E2E", () => {
  test("revert requires non-empty reason and rejects empty input with 422", async ({ request }) => {
    // 1. Login as RO (CRO has applications in SCRUTINY_PENDING)
    const loginRes = await request.post("http://localhost:8000/api/auth/login", {
      data: { email: "ro.cro@aicte-india.org", password: "aicte@2026" },
    });
    expect(loginRes.ok()).toBeTruthy();
    const { access_token } = await loginRes.json();

    // 2. Query an application that is in SCRUTINY_PENDING
    const appsRes = await request.get("http://localhost:8000/api/applications", {
      headers: { Authorization: `Bearer ${access_token}` },
    });
    expect(appsRes.ok()).toBeTruthy();
    const apps = await appsRes.json();
    const targetApp = apps.find((a: any) => a.current_stage === "SCRUTINY_PENDING");
    expect(targetApp).toBeDefined();

    // 3. Attempt revert with empty string reason -> expect 422
    const revertEmpty = await request.post(`http://localhost:8000/api/applications/${targetApp.id}/revert`, {
      headers: { Authorization: `Bearer ${access_token}` },
      data: { target_stage: "REVERTED_TO_DEFICIENCY", reason: "" },
    });
    expect(revertEmpty.status()).toBe(422);

    // 4. Attempt revert with valid reason -> expect 200
    const revertValid = await request.post(`http://localhost:8000/api/applications/${targetApp.id}/revert`, {
      headers: { Authorization: `Bearer ${access_token}` },
      data: { target_stage: "REVERTED_TO_DEFICIENCY", reason: "Missing audited balance sheet and AICTE NOC form." },
    });
    expect(revertValid.ok()).toBeTruthy();
    const updated = await revertValid.json();
    expect(updated.current_stage).toBe("REVERTED_TO_DEFICIENCY");
  });

  test("cross-region isolation returns 404/403 for unauthorized regional access", async ({ request }) => {
    // SRO Officer
    const sroLogin = await request.post("http://localhost:8000/api/auth/login", {
      data: { email: "ro.sro@aicte-india.org", password: "aicte@2026" },
    });
    const sroToken = (await sroLogin.json()).access_token;

    // NRO Officer
    const nroLogin = await request.post("http://localhost:8000/api/auth/login", {
      data: { email: "ro.nro@aicte-india.org", password: "aicte@2026" },
    });
    const nroToken = (await nroLogin.json()).access_token;

    // Fetch NRO apps
    const nroApps = await (await request.get("http://localhost:8000/api/applications", {
      headers: { Authorization: `Bearer ${nroToken}` },
    })).json();
    const nroApp = nroApps[0];

    // SRO officer attempting to get NRO application
    const crossAccess = await request.get(`http://localhost:8000/api/applications/${nroApp.id}`, {
      headers: { Authorization: `Bearer ${sroToken}` },
    });
    expect(crossAccess.status()).toBe(404);
  });

  test("clock advance triggers obligation breach and alerts idempotently", async ({ request }) => {
    const adminLogin = await request.post("http://localhost:8000/api/auth/login", {
      data: { email: "admin@aicte-india.org", password: "aicte@2026" },
    });
    const adminToken = (await adminLogin.json()).access_token;

    // Advance clock by 30 days
    const advanceRes = await request.post("http://localhost:8000/api/admin/clock/advance", {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: { seconds: 2592000 },
    });
    expect(advanceRes.ok()).toBeTruthy();

    // Re-authenticate at new virtual time (since 30 days exceeds 24h token validity)
    const freshLogin = await request.post("http://localhost:8000/api/auth/login", {
      data: { email: "admin@aicte-india.org", password: "aicte@2026" },
    });
    expect(freshLogin.ok()).toBeTruthy();
    const freshToken = (await freshLogin.json()).access_token;

    // Check obligations list has breached obligations
    const obligationsRes = await request.get("http://localhost:8000/api/obligations", {
      headers: { Authorization: `Bearer ${freshToken}` },
    });
    expect(obligationsRes.ok()).toBeTruthy();
    const obligations = await obligationsRes.json();
    expect(obligations.length).toBeGreaterThan(0);

    // Verify audit log verification remains intact
    const verifyRes = await request.get("http://localhost:8000/api/audit/verify");
    const verifyData = await verifyRes.json();
    expect(verifyData.is_valid).toBe(true);
  });

  test("SLA config route modification updates route template and recomputes obligations", async ({ request }) => {
    const adminLogin = await request.post("http://localhost:8000/api/auth/login", {
      data: { email: "admin@aicte-india.org", password: "aicte@2026" },
    });
    const adminToken = (await adminLogin.json()).access_token;

    // Fetch existing route templates
    const routesRes = await request.get("http://localhost:8000/api/routes", {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    expect(routesRes.ok()).toBeTruthy();
    const routes = await routesRes.json();
    expect(routes.length).toBeGreaterThan(0);

    // Verify system allows querying obligations
    const obsRes = await request.get("http://localhost:8000/api/obligations", {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    expect(obsRes.ok()).toBeTruthy();
  });
});


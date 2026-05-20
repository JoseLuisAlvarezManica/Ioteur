export const delay = (ms) => new Promise((r) => setTimeout(r, ms));

export async function pollUntil(fn, { interval = 1000, maxAttempts = 6 } = {}) {
  for (let i = 0; i < maxAttempts; i++) {
    const res = await fn();
    if (res) return res;
    await delay(interval);
  }
  return null;
}

import { devicesApi } from "../api/devices";

export async function waitForDeviceAbsent(deviceId, options) {
  return pollUntil(async () => {
    const list = await devicesApi.getByUser();
    const still = list.find((d) => d.device_uuid === deviceId);
    return !still;
  }, options);
}

export async function waitForDevicePresent(deviceId, options) {
  return pollUntil(async () => {
    const list = await devicesApi.getByUser();
    return list.find((d) => d.device_uuid === deviceId) || null;
  }, options);
}

export async function waitForDeviceStatus(deviceId, expectedStatus, options) {
  return pollUntil(async () => {
    const list = await devicesApi.getByUser();
    const found = list.find((d) => d.device_uuid === deviceId);
    if (!found) return false;
    return found.status === expectedStatus ? found : false;
  }, options);
}

export default { delay, pollUntil, waitForDeviceAbsent, waitForDevicePresent, waitForDeviceStatus };

export interface DeviceTransport {
  sendFirmwareCommand(deviceId: string, firmwareRef: string): Promise<{ ok: boolean; error?: string }>;
}

export const defaultTransport: DeviceTransport = {
  async sendFirmwareCommand(deviceId: string, firmwareRef: string) {
    return { ok: true };
  }
};

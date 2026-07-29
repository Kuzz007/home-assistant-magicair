# MagicAir for Home Assistant

Unofficial Home Assistant integration for the MagicAir cloud, the MagicAir
BS310 base station, and Tion Breezer 4S.

> [!IMPORTANT]
> This project is not affiliated with Tion. It uses the same undocumented cloud
> service as the MagicAir applications. A MagicAir server change may require an
> integration update, and device control requires internet access.

## Supported devices and features

### MagicAir BS310

- CO₂, temperature, and humidity sensors
- indicator backlight control

### Tion Breezer 4S

- turn on and off
- six-speed control
- automatic and manual modes
- heater and target temperature control
- outside-air and recirculation modes
- inlet and outlet temperature
- estimated remaining filter life

## Installation

### HACS custom repository

1. Open HACS in Home Assistant.
2. Select **Integrations**.
3. Open the three-dot menu and select **Custom repositories**.
4. Add `https://github.com/Kuzz007/home-assistant-magicair` as an
   **Integration** repository.
5. Install **MagicAir** and restart Home Assistant.

### Manual installation

Copy `custom_components/magicair` into the `custom_components` directory in
your Home Assistant configuration, then restart Home Assistant.

## Configuration

1. Open **Settings → Devices & services**.
2. Select **Add integration**.
3. Search for **MagicAir**.
4. Enter the email address and password used by the MagicAir mobile app.
5. If the account contains several homes, choose the one to add.

Credentials are stored in the private Home Assistant configuration and are sent
only to the MagicAir authentication service. Diagnostic downloads redact
credentials, tokens, GUIDs, MAC addresses, and serial numbers.

## Compatibility

The initial release targets Home Assistant 2026.7 and later.

## Support

Open an issue and attach the Home Assistant error message or a redacted
diagnostics download. Never post your MagicAir password or access token.

## License

[MIT](LICENSE)

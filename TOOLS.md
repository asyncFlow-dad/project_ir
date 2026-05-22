# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

### IR remote (OpenVPN + SSH)

- VPN profile: `config/vpn/client.ovpn` ([download URL](https://aistages-api-public-prod.s3.ap-northeast-2.amazonaws.com/app/Vpn/openvpn01-TCP4-1188-config.ovpn))
- VPN auth: `config/vpn/auth.txt` (from `remote_server.md`, gitignored)
- Start VPN (background): `sudo ./scripts/vpn-up.sh`
- Stop VPN: `sudo ./scripts/vpn-down.sh`
- SSH: `ssh ir_mac` or `remote_server.md` command → `10.196.197.9:30421`

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)

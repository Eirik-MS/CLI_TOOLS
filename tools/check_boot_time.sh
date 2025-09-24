#!/bin/bash
# Simple boot + system usage report script

OUTFILE="$HOME/boot_report_$(date +%F_%H-%M-%S).log"

{
  echo "===== Boot Report ====="
  echo "Timestamp: $(date)"
  echo

  echo "---- Boot Time ----"
  systemd-analyze
  echo

  echo "---- Critical Chain ----"
  systemd-analyze critical-chain
  echo

  echo "---- Slowest Services (top 20) ----"
  systemd-analyze blame | head -20
  echo

  echo "---- Memory Usage ----"
  free -h
  echo

  echo "---- Disk Usage (root filesystem) ----"
  df -h /
  echo

  echo "---- Snap leftovers ----"
  systemctl --type=service --state=running | grep snap || echo "No snap services running"
  du -sh /var/lib/snapd /snap ~/snap 2>/dev/null || echo "No snap dirs found"
  echo
} | tee "$OUTFILE"

echo "Report saved to $OUTFILE"

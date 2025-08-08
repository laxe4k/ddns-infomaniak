import os
import time
import socket
import requests
from typing import Optional

try:
    import ipaddress
except ImportError:  # pragma: no cover
    ipaddress = None  # type: ignore


class InfomaniakDDNSClient:
    """
    Client orienté objet pour maintenir à jour un enregistrement DNS Infomaniak
    avec l'adresse IP publique actuelle (IPv4/IPv6).
    """

    def __init__(self, hostname: str, username: str, password: str, interval_seconds: int = 300, enable_ipv6: bool = False):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.interval_seconds = max(15, interval_seconds)  # sécurité anti-spam API
        self.enable_ipv6 = enable_ipv6

        self._last_ipv4: Optional[str] = None
        self._last_ipv6: Optional[str] = None

    # --- Public API ---

    def run_forever(self) -> None:
        """Boucle principale: vérifie et met à jour périodiquement."""
        print("DDNS Infomaniak - démarrage du service en boucle continue…")
        print(f"Cible: {self.hostname} | IPv6: {'ON' if self.enable_ipv6 else 'OFF'} | Intervalle: {self.interval_seconds}s")
        while True:
            try:
                self._process_version(4)
                if self.enable_ipv6:
                    self._process_version(6)
            except Exception as exc:  # ne jamais casser la boucle
                print(f"[ERREUR] Exception non gérée dans la boucle principale: {exc}")
            finally:
                time.sleep(self.interval_seconds)

    # --- Internal helpers ---

    def _process_version(self, ip_version: int) -> None:
        ip_label = f"IPv{ip_version}"
        print(f"\n--- Vérification {ip_label} ---")

        public_ip = self._get_public_ip(ip_version)
        if not public_ip:
            print(f"[WARN] Impossible d'obtenir l'IP publique {ip_label}.")
            return

        if ip_version == 6 and ipaddress is not None:
            try:
                ipaddress.IPv6Address(public_ip)
            except Exception:
                print(f"[WARN] IP {ip_label} invalide: {public_ip}")
                return

        current_dns_ip = self._resolve_hostname_ip(self.hostname, ip_version)
        if current_dns_ip:
            print(f"{ip_label} actuelle dans DNS: {current_dns_ip}")
        else:
            print(f"[INFO] Aucun enregistrement {ip_label} existant pour {self.hostname}.")

        if current_dns_ip == public_ip:
            print(f"{ip_label} inchangée ({public_ip}). Aucune mise à jour.")
            self._remember_last(ip_version, public_ip)
            return

        # Anti-boucle: éviter d'appeler l'API si on a déjà tenté avec la même IP récemment
        last = self._last_ipv4 if ip_version == 4 else self._last_ipv6
        if last == public_ip:
            print(f"[INFO] Dernière IP {ip_label} déjà tentée ({public_ip}). On attend le prochain cycle.")
            return

        self._update_infomaniak_dns(public_ip)
        self._remember_last(ip_version, public_ip)

    def _remember_last(self, ip_version: int, ip_value: str) -> None:
        if ip_version == 4:
            self._last_ipv4 = ip_value
        else:
            self._last_ipv6 = ip_value

    def _get_public_ip(self, ip_version: int) -> Optional[str]:
        url = 'https://api.ipify.org?format=json' if ip_version == 4 else 'https://api64.ipify.org?format=json'
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            return r.json().get('ip')
        except requests.exceptions.Timeout:
            print(f"[WARN] Timeout lors de la récupération IP publique v{ip_version}.")
            return None
        except Exception as e:
            print(f"[WARN] Échec récupération IP publique v{ip_version}: {e}")
            return None

    def _resolve_hostname_ip(self, hostname: str, ip_version: int) -> Optional[str]:
        family = socket.AF_INET if ip_version == 4 else socket.AF_INET6
        try:
            info = socket.getaddrinfo(hostname, None, family=family)
            if info:
                return info[0][4][0]
            return None
        except socket.gaierror:
            return None
        except Exception as e:
            print(f"[WARN] Échec résolution DNS {hostname} v{ip_version}: {e}")
            return None

    def _update_infomaniak_dns(self, ip_to_set: str) -> None:
        url = f"https://infomaniak.com/nic/update?hostname={self.hostname}&myip={ip_to_set}"
        headers = {'User-Agent': 'Infomaniak-DDNS/1.0 (+https://github.com/laxe4k/ddns-infomaniak)'}
        try:
            print(f"[INFO] Mise à jour Infomaniak -> {self.hostname} = {ip_to_set}")
            resp = requests.get(url, auth=(self.username, self.password), headers=headers, timeout=15)
            text = (resp.text or '').strip()
            print(f"[DEBUG] HTTP {resp.status_code} - {text}")

            low = text.lower()
            if 'good' in low or 'nochg' in low:
                print("[OK] DNS mis à jour (ou inchangé).")
            elif 'nohost' in low:
                print("[ERREUR] Hôte inconnu chez Infomaniak (nohost).")
            elif 'badauth' in low:
                print("[ERREUR] Identifiants invalides (badauth).")
            elif 'abuse' in low:
                print("[ERREUR] Limite/abuse détecté par Infomaniak.")
            elif 'badagent' in low:
                print("[ERREUR] User-Agent non accepté (badagent).")
            elif 'badsys' in low or '!donator' in low or 'numhost' in low:
                print("[ERREUR] Réponse non supportée / compte non autorisé.")
            elif '911' in low:
                print("[ERREUR] Erreur serveur temporaire (911). À réessayer plus tard.")
            else:
                print("[INFO] Réponse non reconnue, vérifiez manuellement le résultat.")
        except requests.exceptions.Timeout:
            print("[WARN] Timeout requête de mise à jour Infomaniak.")
        except requests.exceptions.HTTPError as e:
            print(f"[ERREUR] HTTP lors de la mise à jour: {e}")
        except Exception as e:
            print(f"[ERREUR] Échec mise à jour DDNS: {e}")


def from_env() -> InfomaniakDDNSClient:
    hostname = os.getenv('INFOMANIAK_DDNS_HOSTNAME', '').strip()
    username = os.getenv('INFOMANIAK_DDNS_USERNAME', '').strip()
    password = os.getenv('INFOMANIAK_DDNS_PASSWORD', '').strip()
    interval = int(os.getenv('DDNS_INTERVAL_SECONDS', '300'))
    enable_ipv6 = os.getenv('DDNS_ENABLE_IPV6', 'false').lower() in ('1', 'true', 'yes', 'on')

    if not hostname or not username or not password:
        raise ValueError("Variables d'environnement manquantes: INFOMANIAK_DDNS_HOSTNAME, INFOMANIAK_DDNS_USERNAME, INFOMANIAK_DDNS_PASSWORD")

    return InfomaniakDDNSClient(hostname, username, password, interval_seconds=interval, enable_ipv6=enable_ipv6)

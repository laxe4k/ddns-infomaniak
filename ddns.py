import socket
import requests
import os
try:
    import ipaddress
except ImportError:
    ipaddress = None # Allows checking for its availability later

def get_public_ip(ip_version=4):
    """Récupère l'adresse IP publique (v4 ou v6) de la machine."""
    service_url = ""
    if ip_version == 4:
        service_url = 'https://api.ipify.org?format=json'
    elif ip_version == 6:
        service_url = 'https://api64.ipify.org?format=json'
    else:
        print(f"Version IP non supportée ({ip_version}). Utilisez 4 ou 6.")
        return None

    try:
        # print(f"Tentative de récupération de l'IP publique v{ip_version} depuis {service_url}")
        response = requests.get(service_url, timeout=10)
        response.raise_for_status()
        public_ip = response.json()['ip']
        # print(f"IP publique v{ip_version} récupérée : {public_ip}")
        return public_ip
    except requests.exceptions.Timeout:
        print(f"Timeout lors de la récupération de l'IP publique v{ip_version} depuis {service_url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération de l'IP publique v{ip_version} : {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Erreur lors de l'analyse de la réponse JSON pour l'IP publique v{ip_version} : {e}")
        return None

def get_hostname_ip_address(hostname, ip_version=4):
    """Récupère l'adresse IP (v4 ou v6) d'un nom d'hôte."""
    family = 0
    if ip_version == 4:
        family = socket.AF_INET
    elif ip_version == 6:
        family = socket.AF_INET6
    else:
        print(f"Version IP non supportée ({ip_version}) pour la résolution de nom d'hôte. Utilisez 4 ou 6.")
        return None

    try:
        # print(f"Tentative de résolution de {hostname} pour IPv{ip_version}...")
        addrinfo = socket.getaddrinfo(hostname, None, family=family)
        if addrinfo:
            ip_address = addrinfo[0][4][0]
            # print(f"Adresse IPv{ip_version} pour {hostname} : {ip_address}")
            return ip_address
        else:
            # print(f"Aucune adresse IPv{ip_version} trouvée pour {hostname} via getaddrinfo.")
            return None
    except socket.gaierror:
        # print(f"Impossible de résoudre {hostname} pour IPv{ip_version} (socket.gaierror). L'enregistrement DNS n'existe peut-être pas.")
        return None
    except Exception as e:
        print(f"Erreur inattendue lors de la résolution de {hostname} pour IPv{ip_version} : {e}")
        return None

def update_infomaniak_dns(hostname_to_update, ip_to_set, username, password):
    """Envoie une requête de mise à jour DNS à Infomaniak avec l'IP spécifiée."""
    if not ip_to_set:
        print(f"Aucune adresse IP fournie pour la mise à jour de {hostname_to_update}. Annulation de la mise à jour.")
        return

    update_url = f"https://infomaniak.com/nic/update?hostname={hostname_to_update}&myip={ip_to_set}"
    try:
        print(f"Envoi de la requête de mise à jour à : {update_url} avec authentification.")
        headers = {'User-Agent': 'Python DDNS Client/1.0 github.com/copilot'} # Example User-Agent
        response = requests.get(update_url, auth=(username, password), headers=headers, timeout=15)
        response.raise_for_status()
        
        print("Réponse d'Infomaniak :")
        print(f"  Status Code: {response.status_code}")
        response_text_clean = response.text.strip()
        print(f"  Contenu: {response_text_clean}")
        
        response_text_lower = response_text_clean.lower()
        if "nochg" in response_text_lower or "good" in response_text_lower:
            print(f"Mise à jour DNS pour {ip_to_set} réussie ou IP déjà à jour pour {hostname_to_update}.")
        elif "abuse" in response_text_lower:
            print("Erreur : Abus détecté par Infomaniak. Trop de requêtes ou autre problème.")
        elif "nohost" in response_text_lower:
            print(f"Erreur : Le nom d'hôte {hostname_to_update} n'existe pas ou n'est pas géré par ce compte.")
        elif "badauth" in response_text_lower:
            print("Erreur : Mauvaise authentification. Vérifiez vos identifiants.")
        elif "badagent" in response_text_lower:
            print("Erreur : User-Agent bloqué. Essayez de spécifier un User-Agent différent dans les headers.")
        elif "badsys" in response_text_lower or "!donator" in response_text_lower or "numhost" in response_text_lower:
            print(f"Erreur de système ou de paramètre avec Infomaniak (ex: {response_text_clean}). Vérifiez les paramètres de la requête: {update_url}")
        elif "911" in response_text_lower:
            print("Erreur : Service Infomaniak temporairement en maintenance (911).")
        else:
            print(f"Réponse inattendue d'Infomaniak pour {hostname_to_update} (IP: {ip_to_set}): {response_text_clean}")
            
    except requests.exceptions.HTTPError as e:
        print(f"Erreur HTTP lors de l'envoi de la requête à Infomaniak pour {hostname_to_update} (IP: {ip_to_set}): {e}")
        if e.response is not None:
            print(f"  Réponse d'Infomaniak (Erreur): Status {e.response.status_code}, Contenu: {e.response.text.strip()}")
    except requests.exceptions.Timeout:
        print(f"Timeout lors de l'envoi de la requête à Infomaniak pour {hostname_to_update} (IP: {ip_to_set}).")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'envoi de la requête à Infomaniak pour {hostname_to_update} (IP: {ip_to_set}): {e}")

def process_ddns_update(ip_version, target_hostname, username, password, ipaddress_module):
    """Traite la mise à jour DDNS pour une version IP donnée (4 ou 6)."""
    ip_type_str = f"IPv{ip_version}"
    print(f"\n--- Traitement {ip_type_str} ---")
    print(f"Récupération de l'adresse {ip_type_str} publique...")
    current_public_ip = get_public_ip(ip_version=ip_version)

    if not current_public_ip:
        print(f"Impossible de récupérer l'adresse {ip_type_str} publique. La mise à jour DNS {ip_type_str} est annulée.")
        return

    # Validation spécifique pour IPv6
    if ip_version == 6:
        is_valid_ipv6_format = False
        if ipaddress_module: # Check if ipaddress module was successfully imported
            try:
                ip_obj = ipaddress_module.ip_address(current_public_ip)
                if ip_obj.version == 6:
                    is_valid_ipv6_format = True
                else:
                    print(f"Avertissement : Le service de détection d'IP publique v6 ('https://api64.ipify.org?format=json') "
                          f"a retourné une adresse IPv4 : {current_public_ip}.")
                    print("  Cela peut indiquer un problème de configuration réseau IPv6 (ex: dans l'environnement Docker) ou que le service a fourni une IP de repli.")
            except ValueError:
                print(f"Avertissement : L'adresse IP '{current_public_ip}' retournée par le service v6 n'est pas une adresse IP valide.")
        else: # Fallback basic check if ipaddress module is not available
            if ":" in current_public_ip and "." not in current_public_ip: # Basic heuristic for IPv6
                is_valid_ipv6_format = True
                print("Avertissement : Le module 'ipaddress' n'est pas disponible. Validation IPv6 basique effectuée.")
            else:
                print(f"Avertissement : Le module 'ipaddress' n'est pas disponible pour une validation robuste. "
                      f"L'adresse '{current_public_ip}' (obtenue pour IPv6) ne semble pas être une IPv6 valide (elle pourrait être une IPv4).")

        if not is_valid_ipv6_format:
            print(f"La mise à jour DNS {ip_type_str} sera ignorée car une adresse {ip_type_str} publique valide n'a pas été obtenue.")
            return # Ne pas continuer pour cette version IP

    print(f"Adresse {ip_type_str} publique actuelle : {current_public_ip}")
    print(f"Récupération de l'adresse {ip_type_str} de {target_hostname} via DNS...")
    remote_ip = get_hostname_ip_address(target_hostname, ip_version=ip_version)

    needs_update = False
    if remote_ip:
        print(f"Adresse {ip_type_str} de {target_hostname} (DNS) : {remote_ip}")
        
        normalized_current = current_public_ip
        normalized_remote = remote_ip
        
        if ip_version == 6:
            if ipaddress_module:
                try:
                    normalized_current = ipaddress_module.ip_address(current_public_ip).compressed
                    normalized_remote = ipaddress_module.ip_address(remote_ip).compressed
                except ValueError as e:
                    print(f"Avertissement : Erreur de normalisation d'une adresse IP ({e}). Utilisation de la comparaison directe en minuscules.")
                    normalized_current = current_public_ip.lower()
                    normalized_remote = remote_ip.lower()
                except Exception as e: 
                    print(f"Avertissement : Erreur inattendue lors de la normalisation IP ({e}). Utilisation de la comparaison directe en minuscules.")
                    normalized_current = current_public_ip.lower()
                    normalized_remote = remote_ip.lower()
            else: # Fallback normalization
                normalized_current = current_public_ip.lower()
                normalized_remote = remote_ip.lower()
        
        if normalized_current != normalized_remote:
            if ip_version == 6:
                print(f"Les adresses {ip_type_str} sont différentes (Publique normalisée: {normalized_current}, DNS normalisée: {normalized_remote}).")
            else:
                print(f"Les adresses {ip_type_str} sont différentes (Publique: {current_public_ip}, DNS: {remote_ip}).")
            needs_update = True
        else:
            if ip_version == 6:
                print(f"Les adresses {ip_type_str} sont identiques (normalisées). Aucune mise à jour {ip_type_str} nécessaire pour {target_hostname}.")
            else:
                print(f"Les adresses {ip_type_str} sont identiques. Aucune mise à jour {ip_type_str} nécessaire pour {target_hostname}.")
    else:
        print(f"Impossible de récupérer l'adresse {ip_type_str} de {target_hostname} via DNS (l'enregistrement n'existe peut-être pas).")
        needs_update = True # Mettre à jour si l'enregistrement distant n'est pas trouvé

    if needs_update:
        print(f"Lancement de la mise à jour DNS {ip_type_str} pour {target_hostname} avec IP {current_public_ip}...")
        update_infomaniak_dns(target_hostname, current_public_ip, username, password)

if __name__ == "__main__":
    target_hostname = os.getenv("INFOMANIAK_DDNS_HOSTNAME")
    infomaniak_username = os.getenv("INFOMANIAK_DDNS_USERNAME")
    infomaniak_password = os.getenv("INFOMANIAK_DDNS_PASSWORD")

    # Traitement IPv4
    process_ddns_update(4, target_hostname, infomaniak_username, infomaniak_password, ipaddress)

    # Traitement IPv6 - Comment out this line to skip IPv6 processing
    # process_ddns_update(6, target_hostname, infomaniak_username, infomaniak_password, ipaddress)

    print("\nScript terminé.")
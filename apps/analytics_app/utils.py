import ipaddress
import urllib.request
import json
import logging
from user_agents import parse

logger = logging.getLogger('linkforge')

def parse_user_agent(user_agent_string: str):
    """
    Parses a user-agent string to extract browser and operating system details.
    """
    if not user_agent_string:
        return "Unknown", "Unknown"
        
    try:
        ua = parse(user_agent_string)
        
        # Format browser string
        browser_family = ua.browser.family
        browser_version = ua.browser.version_string
        browser = f"{browser_family} {browser_version}".strip() if browser_version else browser_family
        
        # Format OS string
        os_family = ua.os.family
        os_version = ua.os.version_string
        os_name = f"{os_family} {os_version}".strip() if os_version else os_family
        
        return browser or "Unknown", os_name or "Unknown"
    except Exception as e:
        logger.error(f"Error parsing user agent '{user_agent_string}': {str(e)}")
        return "Unknown", "Unknown"

def get_country_from_ip(ip: str) -> str:
    """
    Looks up the country corresponding to an IP address using ip-api.com.
    Immediately detects and labels private/loopback IP addresses.
    """
    if not ip or ip in ('127.0.0.1', '::1'):
        return "Localhost"
        
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback:
            return "Local Network"
    except ValueError:
        # Not a valid IP syntax, return Unknown
        return "Unknown"
        
    # Free geolocation lookup API with 2s timeout
    url = f"http://ip-api.com/json/{ip}?fields=status,country"
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'LinkForge/1.0 (Django URL Shortener)'}
        )
        with urllib.request.urlopen(req, timeout=2.0) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if res_data.get('status') == 'success':
                return res_data.get('country', 'Unknown')
    except Exception as e:
        logger.warning(f"Failed to geolocate IP {ip} via API: {str(e)}")
        
    return "Unknown"

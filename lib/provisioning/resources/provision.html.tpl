<!DOCTYPE html>
<html>
<head><title>Mad Max Local Proxy - Provisioning</title></head>
<body>
<h2>Mad Max Local Proxy @ __LAN_IP__</h2>

<h3>Step 1 - Certificates and Wine setup (run once)</h3>
<table border="1" cellpadding="8">
<tr><th>Platform</th><th>One-liner</th><th>Download</th></tr>
<tr>
  <td><b>Steam Deck</b> (SteamOS, Proton)</td>
  <td><pre>curl -o setup_deck.sh http://__LAN_IP__:__HTTP_PORT__/provision/deck &amp;&amp; bash setup_deck.sh</pre>
  Does not require sudo.</td>
  <td><a href="/provision/deck">setup_deck.sh</a></td>
</tr>
<tr>
  <td><b>Windows</b> (native)</td>
  <td><pre>Invoke-WebRequest http://__LAN_IP__:__HTTP_PORT__/provision/windows -OutFile setup.ps1; .\setup.ps1</pre>
  Run as Administrator.</td>
  <td><a href="/provision/windows">setup_windows.ps1</a></td>
</tr>
</table>

<h3>Step 2 - Install systemd service (Steam Deck only)</h3>
<p>
Installs <code>madmax-offline.service</code> so the proxy starts on every boot.<br>
The service automatically sets DNS to the proxy on start, and restores auto-DNS on stop.
</p>
<table border="1" cellpadding="8">
<tr><th>Platform</th><th>One-liner</th><th>Download</th></tr>
<tr>
  <td><b>Steam Deck</b></td>
  <td>
    <pre>curl -o install_service_deck.sh http://__LAN_IP__:__HTTP_PORT__/provision/deck/service &amp;&amp; sudo bash install_service_deck.sh</pre>
    Requires sudo. Edit PROJECT_DIR at the top of the script if your path differs from /home/deck/madmax-2015-offline.
  </td>
  <td><a href="/provision/deck/service">install_service_deck.sh</a></td>
</tr>
</table>

<h3>Uninstall</h3>
<table border="1" cellpadding="8">
<tr><th>Platform</th><th>What it removes</th><th>One-liner</th><th>Download</th></tr>
<tr>
  <td><b>Steam Deck</b> - certificates</td>
  <td>CA from system bundle + Wine/Proton registry + restores DNS</td>
  <td><pre>curl -o uninstall_cert_deck.sh http://__LAN_IP__:__HTTP_PORT__/provision/deck/uninstall &amp;&amp; bash uninstall_cert_deck.sh</pre></td>
  <td><a href="/provision/deck/uninstall">uninstall_cert_deck.sh</a></td>
</tr>
<tr>
  <td><b>Steam Deck</b> - service</td>
  <td>Stops + disables <code>madmax-offline.service</code>, removes unit file, restores DNS</td>
  <td><pre>curl -o uninstall_service_deck.sh http://__LAN_IP__:__HTTP_PORT__/provision/deck/service/uninstall &amp;&amp; sudo bash uninstall_service_deck.sh</pre>
  Requires sudo.</td>
  <td><a href="/provision/deck/service/uninstall">uninstall_service_deck.sh</a></td>
</tr>
<tr>
  <td><b>Windows</b> - certificates</td>
  <td>CA from LocalMachine\Root + restores DNS</td>
  <td><pre>Invoke-WebRequest http://__LAN_IP__:__HTTP_PORT__/provision/windows/uninstall -OutFile uninstall.ps1; .\uninstall.ps1</pre>
  Run as Administrator.</td>
  <td><a href="/provision/windows/uninstall">uninstall_cert_windows.ps1</a></td>
</tr>
</table>

<h3>Other</h3>
<a href="/ca.crt">Download CA certificate only (localproxy_ca.crt)</a>

<h3>Useful service commands</h3>
<pre>
sudo systemctl status madmax-offline
journalctl -u madmax-offline -f
sudo systemctl stop madmax-offline      # stops server and restores DNS
sudo systemctl disable madmax-offline   # remove from autostart
</pre>
</body>
</html>

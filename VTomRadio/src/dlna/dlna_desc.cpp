#include "../core/options.h"
#ifdef USE_DLNA

#include "dlna_desc.h"
#include "dlna_http_guard.h"
#include <WiFiClient.h>
#include <HTTPClient.h>

bool DlnaDescription::resolveControlURL(const String& descUrl, String& outControlUrl) {
  outControlUrl = "";

  HTTPClient http;
  WiFiClient client;

  Serial.printf("[DLNA] GET %s\n", descUrl.c_str());

  String controlPath;
  {
    DlnaHttpGuard lock;
    if (!lock.ok) {
      Serial.println("[DLNA] HTTP mutex timeout");
      return false;
    }

    HTTPClient http;
    WiFiClient client;
    http.setConnectTimeout(2500);
    http.setTimeout(3000);

    if (!http.begin(client, descUrl)) {
      Serial.println("[DLNA] HTTP begin failed");
      return false;
    }

    int code = http.GET();
    if (code != HTTP_CODE_OK) {
      Serial.printf("[DLNA] HTTP error: %d\n", code);
      http.end();
      return false;
    }

    // Teljes body: a stream.available() alapú olvasás TCP szegmentálásnál idő előtt kilépett
    String body = http.getString();
    http.end();

    if (!parseBody(body, controlPath)) {
      Serial.println("[DLNA] ContentDirectory not found");
      return false;
    }
  }

  if (controlPath.startsWith("http://") || controlPath.startsWith("https://")) {
    outControlUrl = controlPath;
  } else {
    if (!controlPath.startsWith("/")) controlPath = "/" + controlPath;
    outControlUrl = extractBaseUrl(descUrl) + controlPath;
  }

  return true;
}

// Sortörés-független: a ContentDirectory service blokkját keresi meg
bool DlnaDescription::parseBody(const String& body, String& outControlPath) {
  int pos = 0;
  while (true) {
    int s1 = body.indexOf("<service>", pos);
    if (s1 < 0) return false;
    int s2 = body.indexOf("</service>", s1);
    if (s2 < 0) return false;
    pos = s2 + 10;

    String blk = body.substring(s1, s2);
    if (blk.indexOf(":service:ContentDirectory:") < 0) continue;

    int a = blk.indexOf("<controlURL>");
    int b = blk.indexOf("</controlURL>");
    if (a < 0 || b <= a) continue;

    outControlPath = blk.substring(a + 12, b);
    outControlPath.trim();
    return outControlPath.length() > 0;
  }
}


String DlnaDescription::extractBaseUrl(const String& fullUrl) {
  // http://IP:PORT/desc/device.xml → http://IP:PORT
  int idx = fullUrl.indexOf('/', 8); // 8 = after http://
  if (idx > 0) return fullUrl.substring(0, idx);
  return fullUrl;
}
#endif // USE_DLNA
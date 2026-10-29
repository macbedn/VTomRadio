#pragma once
#include <Arduino.h>

class DlnaDescription {
public:
  // descUrl = pl. http://IP:PORT/desc/device.xml
  bool resolveControlURL(const String& descUrl, String& outControlUrl);

private:
  bool parseBody(const String& body, String& outControlPath);
  String extractBaseUrl(const String& fullUrl);
};

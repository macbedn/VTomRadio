#ifndef network_h
#define network_h
#include <WiFi.h>
#include <time.h>

enum n_Status_e { CONNECTED, SOFT_AP, FAILED, SDREADY };

class MyNetwork {
  public:
    n_Status_e status;
    struct tm timeinfo;
    bool lostPlaying = false, beginReconnect = false;
    volatile bool justReconnected = false;
    uint32_t disconnectStartMs = 0;
    uint32_t lastScanAttemptMs = 0;
    uint32_t lastWeakSignalScanMs = 0;
    bool weakSignalReconnect = false;
    volatile bool lostEventPending = false;
    bool resumeQueueWarningLogged = false;
    bool scanningOtherNetworks = false;
  public:
    MyNetwork() {};
    void begin();
    void loop();
    void requestTimeSync();
    void requestWeatherSync();
    void setWifiParams();
    bool wifiBegin(bool silent=false);
  private:
    void raiseSoftAP();
    bool wifiBeginWithTimeout(bool silent, uint32_t connectTimeoutMs);
    uint8_t getSortedSavedWifiCandidates(uint8_t* outCandidates, uint8_t maxCandidates);
    static void WiFiLostConnection(WiFiEvent_t event, WiFiEventInfo_t info);
    static void WiFiReconnected(WiFiEvent_t event, WiFiEventInfo_t info);
};

extern MyNetwork network;

void network_get_timeinfo_snapshot(struct tm* out);
void network_set_timeinfo(const struct tm& in);

extern __attribute__((weak)) void network_on_connect();

#endif

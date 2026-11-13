// (MB) Pomiar obciążenia rdzeni: strona /cpu (włączane przez CPU_STATS w myoptions.h)
#pragma once
#include "options.h"
#ifdef CPU_STATS
#    include "../AsyncWebServer/ESPAsyncWebServer.h"
void cpustats_register(AsyncWebServer& server);
#endif

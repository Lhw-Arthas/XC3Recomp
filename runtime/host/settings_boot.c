// Headless boot executable: fixed default settings (the window build reads xcde.ini: settings_ini.c).
#include "../settings.h"

int g_window_w = 1280, g_window_h = 720;
const char *const g_language_codes[N_LANGUAGES] = {"", "ja", "en-US", "fr", "de", "it", "es", "zh-CN", "ko", "nl", "pt", "ru"};
const char *const g_language_names[N_LANGUAGES] = {"Auto", "Japanese", "English", "French", "German", "Italian", "Spanish",
                                                   "Chinese", "Korean", "Dutch", "Portuguese", "Russian"};
Settings g_settings = {.volume = 1.0f, .movie_audio = true};

void settings_load(void) {}
void settings_save(void) {}
#ifndef GAME_DEFAULT_LANGUAGE  // [XC3] the profile's default_language (scripts/build_rt_gfx.sh, settings_ini.c)
#define GAME_DEFAULT_LANGUAGE "en-US"
#endif
const char *settings_language(void) { return GAME_DEFAULT_LANGUAGE; }
const char *settings_language_name(void) { return "English"; }


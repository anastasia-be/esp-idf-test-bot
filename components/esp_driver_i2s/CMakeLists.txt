idf_build_get_property(target IDF_TARGET)

if(${target} STREQUAL "linux")
    return() # This component is not supported by the POSIX/Linux simulator
endif()

set(srcs)
set(include "include")

# I2S related source files
if(CONFIG_SOC_I2S_SUPPORTED)
    list(APPEND srcs "i2s_common.c"
                     "i2s_std.c")
    if(CONFIG_SOC_I2S_SUPPORTS_PDM)
        list(APPEND srcs "i2s_pdm.c")
    endif()
    if(CONFIG_SOC_I2S_SUPPORTS_TDM)
        list(APPEND srcs "i2s_tdm.c")
    endif()
    if(CONFIG_SOC_I2S_SUPPORTS_ETM)
        list(APPEND srcs "i2s_etm.c")
    endif()
endif()

if(CONFIG_SOC_I2S_SUPPORTED OR CONFIG_SOC_LP_I2S_SUPPORTED)
    list(APPEND srcs "i2s_platform.c")
endif()

if(CONFIG_SOC_LP_I2S_SUPPORTED)
    list(APPEND srcs "lp_i2s.c" "lp_i2s_std.c" "lp_i2s_pdm.c")
endif()

if(CONFIG_SOC_LP_I2S_SUPPORT_VAD)
    list(APPEND srcs "lp_i2s_vad.c")
endif()

idf_component_register(SRCS ${srcs}
                    INCLUDE_DIRS ${include}
                    PRIV_REQUIRES esp_driver_gpio esp_pm esp_mm
                    LDFRAGMENTS linker.lf
                    )

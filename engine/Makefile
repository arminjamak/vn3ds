#---------------------------------------------------------------------------------
# vn3ds - 3DS build (devkitARM). Needs: libctru, citro3d, citro2d and the
# portlibs 3ds-zlib, 3ds-libogg, 3ds-libvorbisidec:
#
#   sudo dkp-pacman -S 3ds-dev 3ds-zlib 3ds-libogg 3ds-libvorbisidec
#   make
#
# libopus and opusfile are vendored in third_party/ and built here into
# build/libvnopus.a with their own flags (third_party/opus.mk).
#
# For the desktop test build see Makefile.host.
#---------------------------------------------------------------------------------
.SUFFIXES:

ifeq ($(strip $(DEVKITARM)),)
$(error "Please set DEVKITARM in your environment. export DEVKITARM=<path to>devkitARM")
endif

TOPDIR ?= $(CURDIR)
include $(DEVKITARM)/3ds_rules

TARGET          := vn3ds
BUILD           := build
SOURCES         := source source/3ds
INCLUDES        := source
APP_TITLE       := vn3ds
APP_DESCRIPTION := Ren'Py visual novels in stereoscopic 3D
APP_AUTHOR      := vn3ds
ICON            := icon.png

ARCH     := -march=armv6k -mtune=mpcore -mfloat-abi=hard -mtp=soft
CFLAGS   := -g -Wall -Wno-format-truncation -O2 -mword-relocations -ffunction-sections $(ARCH)
CFLAGS   += $(INCLUDE) -D__3DS__ -std=gnu11 -DVN_HAVE_OPUS -DVN_HAVE_TREMOR
# the release tag (CI: make VERSION=v0.3.0); "dev" builds never update themselves (update.h)
VERSION  ?= dev
CFLAGS   += -DVN3DS_VERSION=\"$(VERSION)\"
CFLAGS   += -I$(TOPDIR)/third_party/opus/include -I$(TOPDIR)/third_party/opusfile/include
CFLAGS   += -I$(TOPDIR)/third_party/pocketpy -DPK_ENABLE_OS=0
ASFLAGS  := -g $(ARCH)
LDFLAGS   = -specs=3dsx.specs -g $(ARCH) -Wl,-Map,$(notdir $*.map)

LIBS     := -lcitro2d -lcitro3d -lvnopus -lvnpy -lvorbisidec -logg -lz -lctru -lm
LIBDIRS  := $(PORTLIBS) $(CTRULIB)

ifneq ($(BUILD),$(notdir $(CURDIR)))

export OUTPUT   := $(CURDIR)/$(TARGET)
export TOPDIR   := $(CURDIR)
export VPATH    := $(foreach dir,$(SOURCES),$(CURDIR)/$(dir))
export DEPSDIR  := $(CURDIR)/$(BUILD)

CFILES          := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.c)))

export LD       := $(CC)
export OFILES   := $(CFILES:.c=.o)
export INCLUDE  := $(foreach dir,$(INCLUDES),-I$(CURDIR)/$(dir)) \
                   $(foreach dir,$(LIBDIRS),-I$(dir)/include) \
                   -I$(CURDIR)/$(BUILD)
export LIBPATHS := $(foreach dir,$(LIBDIRS),-L$(dir)/lib) -L$(CURDIR)/$(BUILD)

export APP_ICON := $(TOPDIR)/$(ICON)
export _3DSXDEPS := $(OUTPUT).smdh
export _3DSXFLAGS += --smdh=$(OUTPUT).smdh

.PHONY: all clean

all: $(BUILD)
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile

$(BUILD):
	@mkdir -p $@

clean:
	@echo clean ...
	@rm -fr $(BUILD) $(TARGET).3dsx $(OUTPUT).smdh $(TARGET).elf

else

DEPENDS := $(OFILES:.o=.d)

$(OUTPUT).3dsx : $(OUTPUT).elf $(_3DSXDEPS)

$(OUTPUT).elf : $(OFILES) libvnopus.a libvnpy.a

#---------------------------------------------------------------------------------
# third-party Opus decoder: its own defines and include paths, warnings off
#---------------------------------------------------------------------------------
TP_DIR    := $(TOPDIR)/third_party
include $(TP_DIR)/opus.mk
TP_OFILES := $(addprefix tp/,$(OPUS_SRC:.c=.o) $(OPUSFILE_SRC:.c=.o))
TP_CFLAGS := -O2 -w -mword-relocations -ffunction-sections -fdata-sections $(ARCH) -std=gnu11

tp/opus/%.o : $(TP_DIR)/opus/%.c
	@mkdir -p $(dir $@)
	@echo $(notdir $<)
	@$(CC) -MMD -MP -MF $(@:.o=.d) $(TP_CFLAGS) $(OPUS_DEFS) $(OPUS_ARM_DEFS) $(OPUS_INCS) -c $< -o $@

tp/opusfile/%.o : $(TP_DIR)/opusfile/%.c
	@mkdir -p $(dir $@)
	@echo $(notdir $<)
	@$(CC) -MMD -MP -MF $(@:.o=.d) $(TP_CFLAGS) $(OPUSFILE_DEFS) $(OPUSFILE_INCS) -I$(PORTLIBS)/include -c $< -o $@

libvnopus.a : $(TP_OFILES)
	@rm -f $@
	@$(AR) rcs $@ $^

# pocketpy (the screen runtime's Python, see source/pyscreen.c): one file
tp/pocketpy.o : $(TP_DIR)/pocketpy/pocketpy.c
	@mkdir -p $(dir $@)
	@echo $(notdir $<)
	@$(CC) -MMD -MP -MF $(@:.o=.d) $(TP_CFLAGS) -DPK_ENABLE_OS=0 -I$(TP_DIR)/pocketpy -c $< -o $@

libvnpy.a : tp/pocketpy.o
	@rm -f $@
	@$(AR) rcs $@ $^

-include $(DEPENDS) $(TP_OFILES:.o=.d) tp/pocketpy.d

endif

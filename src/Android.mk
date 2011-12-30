LOCAL_PATH := $(call my-dir)

##########################################
# dparse, needed by fmbt for Android

include $(CLEAR_VARS)
LOCAL_MODULE := dparse

LOCAL_SRC_FILES :=	\
	d/arg.c		\
	d/parse.c	\
	d/scan.c	\
	d/symtab.c	\
	d/util.c	\
	d/read_binary.c \
	d/dparse_tree.c \
LOCAL_CFLAGS := -DD_MAJOR_VERSION=1 -DD_MINOR_VERSION=26 -DD_BUILD_VERSION=\"\"
include $(BUILD_STATIC_LIBRARY)

##########################################
# fmbt for Android

include $(CLEAR_VARS)
LOCAL_MODULE := fmbt_droid
LOCAL_MODULE_TAGS := optional

include $(LOCAL_PATH)/Sources.mk

LOCAL_SRC_FILES := $(fmbt_droid_SOURCES)

LOCAL_STATIC_LIBRARIES := dparse

LOCAL_SHARED_LIBRARIES := libstlport libdl

LOCAL_C_INCLUDES +=	\
	bionic		\
	$(LOCAL_PATH)/d \
	external/stlport/stlport

LOCAL_CPPFLAGS := -DDROI
LOCAL_LDFLAGS := -Wl,-E -Wl,--no-gc-sections

LOCAL_CPP_EXTENSION := .cc

$(LOCAL_PATH)/d/make_dparser:
	sh -c 'cd $(LOCAL_PATH)/d && make make_dparser'

$(LOCAL_PATH)/%.g.d_parser.cc: $(LOCAL_PATH)/%.g $(LOCAL_PATH)/d/make_dparser
	$(LOCAL_PATH)/d/make_dparser -o $@ -i $* $<

include $(BUILD_EXECUTABLE)

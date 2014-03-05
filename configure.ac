AC_INIT([fmbt], [0.12.3-0.rc0], [antti.kervinen@intel.com])
AM_INIT_AUTOMAKE([foreign -Wall -Werror])

AC_CONFIG_MACRO_DIR([m4])

m4_pattern_allow([AM_PROG_AR])
AM_PROG_AR
AC_PROG_CC
AC_PROG_CXX
AM_PROG_LEX
AC_PROG_LIBTOOL
AC_CONFIG_HEADERS([config.h])

LT_INIT(win32-dll)

# TODO: configurable readline?
# here we could fall back to reading standard input in READLINE,
# see test_engine.cc.
PKG_CHECK_MODULES([LIBEDIT], [libedit], [],
    AC_MSG_FAILURE([libedit required.]))

AC_CHECK_LIB([rt], [clock_gettime])

AC_ARG_ENABLE(rdrnd, AC_HELP_STRING([--enable-rdrnd],
    [enable intel hw random]), [enable_rdrnd=${enableval}])
AM_CONDITIONAL(RDRND, test "${enable_rdrnd}" = "yes")

AC_ARG_ENABLE(android, AC_HELP_STRING([--enable-android],
    [enable building fmbt_droid]), [enable_android=${enableval}])
AM_CONDITIONAL(ANDROID, test "${enable_android}" = "yes")


AC_ARG_WITH([ndk-build],
            [AS_HELP_STRING([--with-ndk-build=/path/and/executable], [ndk-build for building Android binary])],
            [NDK_BUILD="$withval"],
            [NDK_BUILD="ndk-build"])

AC_SUBST([NDK_BUILD])


AC_SUBST([FMBT_VERSION], ['AC_PACKAGE_VERSION'])

AC_ARG_WITH([build-info],
            [AS_HELP_STRING([--with-build-info=string], [add extra build/version info])],
            [FMBTBUILDINFO=$withval],
            [FMBTBUILDINFO=m4_esyscmd_s([head -n 1 configure.ac | grep -q rc0 && echo -n \-&& git describe --always])])
AC_SUBST([FMBTBUILDINFO])


AS_IF([test "x$enable_android" != "xyes"],
    [PKG_CHECK_MODULES([GLIB], [glib-2.0], [],
        AC_MSG_FAILURE([glib-2.0 required if not --enable-android]))]

    [PKG_CHECK_MODULES([GOBJECT], [gobject-2.0], [],
        AC_MSG_FAILURE([gobject-2.0 required if not --enable-android]))]

    [PKG_CHECK_MODULES([MAGIC], [Magick++], [],
        AC_MSG_FAILURE([Magick++ required if not --enable-android]))]

    [PKG_CHECK_MODULES([XML2], [libxml-2.0], [],
        AC_MSG_FAILURE([libxml-2.0 required if not --enable-android]))]
    )


if test -z "$JVMLDFLAGS"; then
AC_ARG_WITH([jvm-lib],
            [AS_HELP_STRING([--with-jvm-lib=/path/to/libjvm.so], [directory containing the JVM library, needed to enable AAL/Java support])],
	    [JVMLDFLAGS="-L$withval -ljvm"
	    AC_DEFINE(WITH_JVM,1,[compile with libjvm])],
	    [JVMLDFLAGS=""])
fi
AC_SUBST([JVMLDFLAGS])


AC_ARG_WITH([jvm-include-dir],
            [AS_HELP_STRING([--with-jvm-include-dir=/path/to/jni.h], [directory containing JVM headers])],
	    [JVMCFLAGS="-I$withval -I$withval/linux"
	    AC_DEFINE(WITH_JVM,1,[compile with libjvm])],
	    [JVMCFLAGS=""])

AC_SUBST([JVMCFLAGS])


AC_CONFIG_FILES([
        Makefile
        src/Makefile
        utils/Makefile
        pythonshare/Makefile
        test/Makefile
        examples/Makefile
        fMBT.spec
	utils/fmbt_config.py
        ])


AM_CONDITIONAL([HAVE_PYTHON], [test "$PYTHON" != :])
AM_PATH_PYTHON([2.6],, [:])

AC_ARG_WITH([imagemagick],
  [AS_HELP_STRING([--without-imagemagick],
    [disable eyenfinger icon recognition])],
  [],
  [with_imagemagick="yes"])

AS_IF([test "x$with_imagemagick" != "xno"],
  [PKG_CHECK_MODULES([MAGICK], [Magick++], [],
     [AC_MSG_FAILURE([ImageMagick not found.])])])

AM_CONDITIONAL([HAVE_MAGICK], [test "x$with_imagemagick" != "xno"])

AC_OUTPUT

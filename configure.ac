AC_INIT([fmbt], [0.1rc6], [antti.kervinen@intel.com])
AM_INIT_AUTOMAKE([foreign -Wall -Werror])

AC_CONFIG_MACRO_DIR([m4])

AC_PROG_CC
AC_PROG_CXX
AC_PROG_LIBTOOL
AC_CONFIG_HEADERS([config.h])

# TODO: configurable readline?
# here we could fall back to reading standard input in READLINE,
# see test_engine.cc.
PKG_CHECK_MODULES([LIBEDIT], [libedit], [],
    AC_MSG_FAILURE([libedit required.]))

AC_ARG_ENABLE(android, AC_HELP_STRING([--enable-android],
    [enable building fmbt_droid]), [enable_android=${enableval}])
AM_CONDITIONAL(ANDROID, test "${enable_android}" = "yes")

AC_ARG_WITH([ndk-build],
            [AS_HELP_STRING([--with-ndk-build=/path/and/executable], [ndk-build for building Android binary])],
            [NDK_BUILD="$withval"],
            [NDK_BUILD="ndk-build"])
AC_SUBST([NDK_BUILD])

AS_IF([test "x$enable_android" != "xyes"],
    PKG_CHECK_MODULES([GLIB], [glib-2.0], [],
        AC_MSG_FAILURE([glib-2.0 required if not --enable-android]))

#    AC_LANG_PUSH([C++])
#    AC_CHECK_HEADERS([boost/regex.h], [],
#        [AC_MSG_ERROR(libboost required.)])
#    AC_LANG_POP([C++])
    )

AC_CONFIG_FILES([Makefile src/Makefile utils/Makefile test/Makefile])

AM_CONDITIONAL([HAVE_PYTHON], [test "$PYTHON" != :])
AM_PATH_PYTHON([2.6],, [:])

AC_OUTPUT

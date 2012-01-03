#define  ASSERT_EQ(x,v) \
    if (!((x)==(v))) {                                 \
        log.print("ASSERT_EQ failed: %d != %d", x, v); \
        return 0;                                      \
    }

#define  ASSERT_NEQ(x,v) \
    if ((x)==(v)) {                                     \
        log.print("ASSERT_NEQ failed: %d != %d", x, v); \
        return 0;                                       \
    }

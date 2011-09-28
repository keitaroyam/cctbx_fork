LIBTBX_ANTLR3="../../../antlr3"
gcc -c -I $LIBTBX_ANTLR3/include/ \
  "$LIBTBX_ANTLR3/src/antlr3baserecognizer.c"\
  "$LIBTBX_ANTLR3/src/antlr3basetree.c"\
  "$LIBTBX_ANTLR3/src/antlr3basetreeadaptor.c"\
  "$LIBTBX_ANTLR3/src/antlr3bitset.c"\
  "$LIBTBX_ANTLR3/src/antlr3collections.c"\
  "$LIBTBX_ANTLR3/src/antlr3commontoken.c"\
  "$LIBTBX_ANTLR3/src/antlr3commontree.c"\
  "$LIBTBX_ANTLR3/src/antlr3commontreeadaptor.c"\
  "$LIBTBX_ANTLR3/src/antlr3commontreenodestream.c"\
  "$LIBTBX_ANTLR3/src/antlr3convertutf.c"\
  "$LIBTBX_ANTLR3/src/antlr3cyclicdfa.c"\
  "$LIBTBX_ANTLR3/src/antlr3debughandlers.c"\
  "$LIBTBX_ANTLR3/src/antlr3encodings.c"\
  "$LIBTBX_ANTLR3/src/antlr3exception.c"\
  "$LIBTBX_ANTLR3/src/antlr3filestream.c"\
  "$LIBTBX_ANTLR3/src/antlr3inputstream.c"\
  "$LIBTBX_ANTLR3/src/antlr3intstream.c"\
  "$LIBTBX_ANTLR3/src/antlr3lexer.c"\
  "$LIBTBX_ANTLR3/src/antlr3parser.c"\
  "$LIBTBX_ANTLR3/src/antlr3rewritestreams.c"\
  "$LIBTBX_ANTLR3/src/antlr3string.c"\
  "$LIBTBX_ANTLR3/src/antlr3stringstream.c"\
  "$LIBTBX_ANTLR3/src/antlr3tokenstream.c"\
  "$LIBTBX_ANTLR3/src/antlr3treeparser.c"\
  "$LIBTBX_ANTLR3/src/antlr3ucs2inputstream.c"

ar -r libantlr3.a            \
antlr3baserecognizer.o       \
antlr3commontree.o           \
antlr3encodings.o            \
antlr3parser.o               \
antlr3ucs2inputstream.o      \
antlr3basetree.o             \
antlr3commontreeadaptor.o    \
antlr3exception.o            \
antlr3rewritestreams.o       \
antlr3basetreeadaptor.o      \
antlr3commontreenodestream.o \
antlr3filestream.o           \
antlr3string.o               \
antlr3bitset.o               \
antlr3convertutf.o           \
antlr3inputstream.o          \
antlr3stringstream.o         \
antlr3collections.o          \
antlr3cyclicdfa.o            \
antlr3intstream.o            \
antlr3tokenstream.o          \
antlr3commontoken.o          \
antlr3debughandlers.o        \
antlr3lexer.o                \
antlr3treeparser.o

g++ -o cif_parser -I $LIBTBX_ANTLR3/include/ -I ../../ main.cpp \
../cifLexer.cpp ../cifParser.cpp ../cifWalker.cpp libantlr3.a

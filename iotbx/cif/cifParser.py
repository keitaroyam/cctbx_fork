# $ANTLR 3.1.2 cif.g 2010-05-04 17:43:59

import sys
from antlr3 import *
from antlr3.compat import set, frozenset

import iotbx.cif
from cctbx.array_family import flex



# for convenience in actions
HIDDEN = BaseRecognizer.HIDDEN

# token types
DOUBLE_QUOTED_STRING=29
CHAR_STRING=13
EXPONENT=12
NON_BLANK_CHAR=27
SEMI_COLON_TEXT_FIELD=14
SINGLE_QUOTED_STRING=28
DOUBLE_QUOTE=16
GLOBAL_=24
ORDINARY_CHAR=18
WHITESPACE=5
SAVE=7
VERSION=26
EOF=-1
TAG=8
SINGLE_QUOTE=17
T__31=31
T__32=32
STOP_=25
EOL=15
T__33=33
NON_BLANK_CHAR_=19
T__34=34
T__35=35
COMMENTS=4
T__36=36
SAVE_FRAME_HEADING=6
SAVE_=23
ANY_PRINT_CHAR=21
TEXT_LEAD_CHAR=20
LOOP_=10
DIGIT=11
UNQUOTED_STRING=30
DATA_=22
DATA_BLOCK_HEADING=9

# token names
tokenNames = [
    "<invalid>", "<EOR>", "<DOWN>", "<UP>",
    "COMMENTS", "WHITESPACE", "SAVE_FRAME_HEADING", "SAVE", "TAG", "DATA_BLOCK_HEADING",
    "LOOP_", "DIGIT", "EXPONENT", "CHAR_STRING", "SEMI_COLON_TEXT_FIELD",
    "EOL", "DOUBLE_QUOTE", "SINGLE_QUOTE", "ORDINARY_CHAR", "NON_BLANK_CHAR_",
    "TEXT_LEAD_CHAR", "ANY_PRINT_CHAR", "DATA_", "SAVE_", "GLOBAL_", "STOP_",
    "VERSION", "NON_BLANK_CHAR", "SINGLE_QUOTED_STRING", "DOUBLE_QUOTED_STRING",
    "UNQUOTED_STRING", "'.'", "'?'", "'-'", "'+'", "'('", "')'"
]




class cifParser(Parser):
    grammarFileName = "cif.g"
    antlr_version = version_str_to_tuple("3.1.2")
    antlr_version_str = "3.1.2"
    tokenNames = tokenNames

    def __init__(self, input, state=None):
        if state is None:
            state = RecognizerSharedState()

        Parser.__init__(self, input, state)


        self.dfa8 = self.DFA8(
            self, 8,
            eot = self.DFA8_eot,
            eof = self.DFA8_eof,
            min = self.DFA8_min,
            max = self.DFA8_max,
            accept = self.DFA8_accept,
            special = self.DFA8_special,
            transition = self.DFA8_transition
            )

        self.dfa10 = self.DFA10(
            self, 10,
            eot = self.DFA10_eot,
            eof = self.DFA10_eof,
            min = self.DFA10_min,
            max = self.DFA10_max,
            accept = self.DFA10_accept,
            special = self.DFA10_special,
            transition = self.DFA10_transition
            )

        self.dfa16 = self.DFA16(
            self, 16,
            eot = self.DFA16_eot,
            eof = self.DFA16_eof,
            min = self.DFA16_min,
            max = self.DFA16_max,
            accept = self.DFA16_accept,
            special = self.DFA16_special,
            transition = self.DFA16_transition
            )

        self.dfa18 = self.DFA18(
            self, 18,
            eot = self.DFA18_eot,
            eof = self.DFA18_eof,
            min = self.DFA18_min,
            max = self.DFA18_max,
            accept = self.DFA18_accept,
            special = self.DFA18_special,
            transition = self.DFA18_transition
            )

        self.dfa27 = self.DFA27(
            self, 27,
            eot = self.DFA27_eot,
            eof = self.DFA27_eof,
            min = self.DFA27_min,
            max = self.DFA27_max,
            accept = self.DFA27_accept,
            special = self.DFA27_special,
            transition = self.DFA27_transition
            )

        self.dfa25 = self.DFA25(
            self, 25,
            eot = self.DFA25_eot,
            eof = self.DFA25_eof,
            min = self.DFA25_min,
            max = self.DFA25_max,
            accept = self.DFA25_accept,
            special = self.DFA25_special,
            transition = self.DFA25_transition
            )

        self.dfa28 = self.DFA28(
            self, 28,
            eot = self.DFA28_eot,
            eof = self.DFA28_eof,
            min = self.DFA28_min,
            max = self.DFA28_max,
            accept = self.DFA28_accept,
            special = self.DFA28_special,
            transition = self.DFA28_transition
            )

        self.dfa30 = self.DFA30(
            self, 30,
            eot = self.DFA30_eot,
            eof = self.DFA30_eof,
            min = self.DFA30_min,
            max = self.DFA30_max,
            accept = self.DFA30_accept,
            special = self.DFA30_special,
            transition = self.DFA30_transition
            )













    # $ANTLR start "parse"
    # cif.g:27:1: parse[builder] : cif ;
    def parse(self, builder):

        self.builder = builder
        try:
            try:
                # cif.g:29:2: ( cif )
                # cif.g:29:4: cif
                pass
                self._state.following.append(self.FOLLOW_cif_in_parse44)
                self.cif()

                self._state.following.pop()




            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "parse"


    # $ANTLR start "cif"
    # cif.g:34:1: cif : ( COMMENTS )? ( WHITESPACE )* ( data_block ( ( WHITESPACE )* data_block )* ( WHITESPACE )? )? EOF ;
    def cif(self, ):

        try:
            try:
                # cif.g:35:2: ( ( COMMENTS )? ( WHITESPACE )* ( data_block ( ( WHITESPACE )* data_block )* ( WHITESPACE )? )? EOF )
                # cif.g:35:4: ( COMMENTS )? ( WHITESPACE )* ( data_block ( ( WHITESPACE )* data_block )* ( WHITESPACE )? )? EOF
                pass
                # cif.g:35:4: ( COMMENTS )?
                alt1 = 2
                LA1_0 = self.input.LA(1)

                if (LA1_0 == COMMENTS) :
                    alt1 = 1
                if alt1 == 1:
                    # cif.g:35:5: COMMENTS
                    pass
                    self.match(self.input, COMMENTS, self.FOLLOW_COMMENTS_in_cif57)



                # cif.g:35:16: ( WHITESPACE )*
                while True: #loop2
                    alt2 = 2
                    LA2_0 = self.input.LA(1)

                    if (LA2_0 == WHITESPACE) :
                        alt2 = 1


                    if alt2 == 1:
                        # cif.g:35:17: WHITESPACE
                        pass
                        self.match(self.input, WHITESPACE, self.FOLLOW_WHITESPACE_in_cif62)


                    else:
                        break #loop2


                # cif.g:35:30: ( data_block ( ( WHITESPACE )* data_block )* ( WHITESPACE )? )?
                alt6 = 2
                LA6_0 = self.input.LA(1)

                if (LA6_0 == DATA_BLOCK_HEADING) :
                    alt6 = 1
                if alt6 == 1:
                    # cif.g:35:32: data_block ( ( WHITESPACE )* data_block )* ( WHITESPACE )?
                    pass
                    self._state.following.append(self.FOLLOW_data_block_in_cif68)
                    self.data_block()

                    self._state.following.pop()
                    # cif.g:35:43: ( ( WHITESPACE )* data_block )*
                    while True: #loop4
                        alt4 = 2
                        LA4_0 = self.input.LA(1)

                        if (LA4_0 == WHITESPACE) :
                            LA4_1 = self.input.LA(2)

                            if (LA4_1 == WHITESPACE or LA4_1 == DATA_BLOCK_HEADING) :
                                alt4 = 1


                        elif (LA4_0 == DATA_BLOCK_HEADING) :
                            alt4 = 1


                        if alt4 == 1:
                            # cif.g:35:45: ( WHITESPACE )* data_block
                            pass
                            # cif.g:35:45: ( WHITESPACE )*
                            while True: #loop3
                                alt3 = 2
                                LA3_0 = self.input.LA(1)

                                if (LA3_0 == WHITESPACE) :
                                    alt3 = 1


                                if alt3 == 1:
                                    # cif.g:35:45: WHITESPACE
                                    pass
                                    self.match(self.input, WHITESPACE, self.FOLLOW_WHITESPACE_in_cif72)


                                else:
                                    break #loop3


                            self._state.following.append(self.FOLLOW_data_block_in_cif75)
                            self.data_block()

                            self._state.following.pop()


                        else:
                            break #loop4


                    # cif.g:35:71: ( WHITESPACE )?
                    alt5 = 2
                    LA5_0 = self.input.LA(1)

                    if (LA5_0 == WHITESPACE) :
                        alt5 = 1
                    if alt5 == 1:
                        # cif.g:35:72: WHITESPACE
                        pass
                        self.match(self.input, WHITESPACE, self.FOLLOW_WHITESPACE_in_cif81)






                self.match(self.input, EOF, self.FOLLOW_EOF_in_cif88)




            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "cif"


    # $ANTLR start "loop_body"
    # cif.g:38:1: loop_body : v1= value ( ( WHITESPACE )+ v2= value )* ;
    def loop_body(self, ):

        v1 = None

        v2 = None


        self.curr_loop_values = flex.std_string()
        try:
            try:
                # cif.g:40:2: (v1= value ( ( WHITESPACE )+ v2= value )* )
                # cif.g:40:4: v1= value ( ( WHITESPACE )+ v2= value )*
                pass
                self._state.following.append(self.FOLLOW_value_in_loop_body106)
                v1 = self.value()

                self._state.following.pop()
                #action start
                self.curr_loop_values.append(str(((v1 is not None) and [self.input.toString(v1.start,v1.stop)] or [None])[0]))
                #action end
                # cif.g:42:8: ( ( WHITESPACE )+ v2= value )*
                while True: #loop8
                    alt8 = 2
                    alt8 = self.dfa8.predict(self.input)
                    if alt8 == 1:
                        # cif.g:42:10: ( WHITESPACE )+ v2= value
                        pass
                        # cif.g:42:10: ( WHITESPACE )+
                        cnt7 = 0
                        while True: #loop7
                            alt7 = 2
                            LA7_0 = self.input.LA(1)

                            if (LA7_0 == WHITESPACE) :
                                alt7 = 1


                            if alt7 == 1:
                                # cif.g:42:10: WHITESPACE
                                pass
                                self.match(self.input, WHITESPACE, self.FOLLOW_WHITESPACE_in_loop_body119)


                            else:
                                if cnt7 >= 1:
                                    break #loop7

                                eee = EarlyExitException(7, self.input)
                                raise eee

                            cnt7 += 1


                        self._state.following.append(self.FOLLOW_value_in_loop_body133)
                        v2 = self.value()

                        self._state.following.pop()
                        #action start
                        self.curr_loop_values.append(str(((v2 is not None) and [self.input.toString(v2.start,v2.stop)] or [None])[0]))
                        #action end


                    else:
                        break #loop8






            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "loop_body"


    # $ANTLR start "save_frame"
    # cif.g:48:1: save_frame : SAVE_FRAME_HEADING ( ( WHITESPACE )+ data_items )+ ( WHITESPACE )+ SAVE ;
    def save_frame(self, ):

        try:
            try:
                # cif.g:49:2: ( SAVE_FRAME_HEADING ( ( WHITESPACE )+ data_items )+ ( WHITESPACE )+ SAVE )
                # cif.g:49:4: SAVE_FRAME_HEADING ( ( WHITESPACE )+ data_items )+ ( WHITESPACE )+ SAVE
                pass
                self.match(self.input, SAVE_FRAME_HEADING, self.FOLLOW_SAVE_FRAME_HEADING_in_save_frame157)
                # cif.g:49:23: ( ( WHITESPACE )+ data_items )+
                cnt10 = 0
                while True: #loop10
                    alt10 = 2
                    alt10 = self.dfa10.predict(self.input)
                    if alt10 == 1:
                        # cif.g:49:25: ( WHITESPACE )+ data_items
                        pass
                        # cif.g:49:25: ( WHITESPACE )+
                        cnt9 = 0
                        while True: #loop9
                            alt9 = 2
                            LA9_0 = self.input.LA(1)

                            if (LA9_0 == WHITESPACE) :
                                alt9 = 1


                            if alt9 == 1:
                                # cif.g:49:25: WHITESPACE
                                pass
                                self.match(self.input, WHITESPACE, self.FOLLOW_WHITESPACE_in_save_frame161)


                            else:
                                if cnt9 >= 1:
                                    break #loop9

                                eee = EarlyExitException(9, self.input)
                                raise eee

                            cnt9 += 1


                        self._state.following.append(self.FOLLOW_data_items_in_save_frame164)
                        self.data_items()

                        self._state.following.pop()


                    else:
                        if cnt10 >= 1:
                            break #loop10

                        eee = EarlyExitException(10, self.input)
                        raise eee

                    cnt10 += 1


                # cif.g:49:51: ( WHITESPACE )+
                cnt11 = 0
                while True: #loop11
                    alt11 = 2
                    LA11_0 = self.input.LA(1)

                    if (LA11_0 == WHITESPACE) :
                        alt11 = 1


                    if alt11 == 1:
                        # cif.g:49:51: WHITESPACE
                        pass
                        self.match(self.input, WHITESPACE, self.FOLLOW_WHITESPACE_in_save_frame169)


                    else:
                        if cnt11 >= 1:
                            break #loop11

                        eee = EarlyExitException(11, self.input)
                        raise eee

                    cnt11 += 1


                self.match(self.input, SAVE, self.FOLLOW_SAVE_in_save_frame172)




            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "save_frame"


    # $ANTLR start "data_items"
    # cif.g:51:1: data_items : ( TAG WHITESPACE value | loop_header ( WHITESPACE )* loop_body );
    def data_items(self, ):

        TAG1 = None
        value2 = None

        loop_header3 = None


        try:
            try:
                # cif.g:52:2: ( TAG WHITESPACE value | loop_header ( WHITESPACE )* loop_body )
                alt13 = 2
                LA13_0 = self.input.LA(1)

                if (LA13_0 == TAG) :
                    alt13 = 1
                elif (LA13_0 == LOOP_) :
                    alt13 = 2
                else:
                    nvae = NoViableAltException("", 13, 0, self.input)

                    raise nvae

                if alt13 == 1:
                    # cif.g:52:4: TAG WHITESPACE value
                    pass
                    TAG1=self.match(self.input, TAG, self.FOLLOW_TAG_in_data_items182)
                    self.match(self.input, WHITESPACE, self.FOLLOW_WHITESPACE_in_data_items184)
                    self._state.following.append(self.FOLLOW_value_in_data_items186)
                    value2 = self.value()

                    self._state.following.pop()
                    #action start
                    self.builder.add_data_item(TAG1.text, ((value2 is not None) and [self.input.toString(value2.start,value2.stop)] or [None])[0])
                    #action end


                elif alt13 == 2:
                    # cif.g:54:10: loop_header ( WHITESPACE )* loop_body
                    pass
                    self._state.following.append(self.FOLLOW_loop_header_in_data_items199)
                    loop_header3 = self.loop_header()

                    self._state.following.pop()
                    # cif.g:54:22: ( WHITESPACE )*
                    while True: #loop12
                        alt12 = 2
                        LA12_0 = self.input.LA(1)

                        if (LA12_0 == WHITESPACE) :
                            alt12 = 1


                        if alt12 == 1:
                            # cif.g:54:22: WHITESPACE
                            pass
                            self.match(self.input, WHITESPACE, self.FOLLOW_WHITESPACE_in_data_items201)


                        else:
                            break #loop12


                    self._state.following.append(self.FOLLOW_loop_body_in_data_items204)
                    self.loop_body()

                    self._state.following.pop()
                    #action start

                    self.builder.add_loop(((loop_header3 is not None) and [self.input.toString(loop_header3.start,loop_header3.stop)] or [None])[0], data=self.curr_loop_values)

                    #action end



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "data_items"


    # $ANTLR start "data_block"
    # cif.g:60:1: data_block : DATA_BLOCK_HEADING ( ( WHITESPACE )+ ( data_items | save_frame ) )* ;
    def data_block(self, ):

        DATA_BLOCK_HEADING4 = None

        try:
            try:
                # cif.g:61:2: ( DATA_BLOCK_HEADING ( ( WHITESPACE )+ ( data_items | save_frame ) )* )
                # cif.g:61:4: DATA_BLOCK_HEADING ( ( WHITESPACE )+ ( data_items | save_frame ) )*
                pass
                DATA_BLOCK_HEADING4=self.match(self.input, DATA_BLOCK_HEADING, self.FOLLOW_DATA_BLOCK_HEADING_in_data_block217)
                #action start
                self.builder.add_data_block(DATA_BLOCK_HEADING4.text)
                #action end
                # cif.g:63:8: ( ( WHITESPACE )+ ( data_items | save_frame ) )*
                while True: #loop16
                    alt16 = 2
                    alt16 = self.dfa16.predict(self.input)
                    if alt16 == 1:
                        # cif.g:63:10: ( WHITESPACE )+ ( data_items | save_frame )
                        pass
                        # cif.g:63:10: ( WHITESPACE )+
                        cnt14 = 0
                        while True: #loop14
                            alt14 = 2
                            LA14_0 = self.input.LA(1)

                            if (LA14_0 == WHITESPACE) :
                                alt14 = 1


                            if alt14 == 1:
                                # cif.g:63:10: WHITESPACE
                                pass
                                self.match(self.input, WHITESPACE, self.FOLLOW_WHITESPACE_in_data_block230)


                            else:
                                if cnt14 >= 1:
                                    break #loop14

                                eee = EarlyExitException(14, self.input)
                                raise eee

                            cnt14 += 1


                        # cif.g:63:22: ( data_items | save_frame )
                        alt15 = 2
                        LA15_0 = self.input.LA(1)

                        if (LA15_0 == TAG or LA15_0 == LOOP_) :
                            alt15 = 1
                        elif (LA15_0 == SAVE_FRAME_HEADING) :
                            alt15 = 2
                        else:
                            nvae = NoViableAltException("", 15, 0, self.input)

                            raise nvae

                        if alt15 == 1:
                            # cif.g:63:24: data_items
                            pass
                            self._state.following.append(self.FOLLOW_data_items_in_data_block235)
                            self.data_items()

                            self._state.following.pop()


                        elif alt15 == 2:
                            # cif.g:63:37: save_frame
                            pass
                            self._state.following.append(self.FOLLOW_save_frame_in_data_block239)
                            self.save_frame()

                            self._state.following.pop()





                    else:
                        break #loop16






            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "data_block"

    class loop_header_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)





    # $ANTLR start "loop_header"
    # cif.g:66:1: loop_header : LOOP_ ( ( WHITESPACE )+ TAG )+ WHITESPACE ;
    def loop_header(self, ):

        retval = self.loop_header_return()
        retval.start = self.input.LT(1)

        try:
            try:
                # cif.g:67:2: ( LOOP_ ( ( WHITESPACE )+ TAG )+ WHITESPACE )
                # cif.g:67:4: LOOP_ ( ( WHITESPACE )+ TAG )+ WHITESPACE
                pass
                self.match(self.input, LOOP_, self.FOLLOW_LOOP__in_loop_header255)
                # cif.g:67:10: ( ( WHITESPACE )+ TAG )+
                cnt18 = 0
                while True: #loop18
                    alt18 = 2
                    alt18 = self.dfa18.predict(self.input)
                    if alt18 == 1:
                        # cif.g:67:12: ( WHITESPACE )+ TAG
                        pass
                        # cif.g:67:12: ( WHITESPACE )+
                        cnt17 = 0
                        while True: #loop17
                            alt17 = 2
                            LA17_0 = self.input.LA(1)

                            if (LA17_0 == WHITESPACE) :
                                alt17 = 1


                            if alt17 == 1:
                                # cif.g:67:12: WHITESPACE
                                pass
                                self.match(self.input, WHITESPACE, self.FOLLOW_WHITESPACE_in_loop_header259)


                            else:
                                if cnt17 >= 1:
                                    break #loop17

                                eee = EarlyExitException(17, self.input)
                                raise eee

                            cnt17 += 1


                        self.match(self.input, TAG, self.FOLLOW_TAG_in_loop_header262)


                    else:
                        if cnt18 >= 1:
                            break #loop18

                        eee = EarlyExitException(18, self.input)
                        raise eee

                    cnt18 += 1


                self.match(self.input, WHITESPACE, self.FOLLOW_WHITESPACE_in_loop_header267)



                retval.stop = self.input.LT(-1)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return retval

    # $ANTLR end "loop_header"


    # $ANTLR start "inapplicable"
    # cif.g:74:1: inapplicable : '.' ;
    def inapplicable(self, ):

        try:
            try:
                # cif.g:75:2: ( '.' )
                # cif.g:75:4: '.'
                pass
                self.match(self.input, 31, self.FOLLOW_31_in_inapplicable282)




            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "inapplicable"


    # $ANTLR start "unknown"
    # cif.g:77:1: unknown : '?' ;
    def unknown(self, ):

        try:
            try:
                # cif.g:77:9: ( '?' )
                # cif.g:77:11: '?'
                pass
                self.match(self.input, 32, self.FOLLOW_32_in_unknown291)




            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "unknown"

    class value_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)





    # $ANTLR start "value"
    # cif.g:79:1: value : ( inapplicable | unknown | '-' | char_string | numeric | text_field );
    def value(self, ):

        retval = self.value_return()
        retval.start = self.input.LT(1)

        try:
            try:
                # cif.g:79:8: ( inapplicable | unknown | '-' | char_string | numeric | text_field )
                alt19 = 6
                LA19 = self.input.LA(1)
                if LA19 == 31:
                    LA19_1 = self.input.LA(2)

                    if (LA19_1 == EOF or LA19_1 == WHITESPACE or LA19_1 == DATA_BLOCK_HEADING) :
                        alt19 = 1
                    elif (LA19_1 == DIGIT) :
                        alt19 = 5
                    else:
                        nvae = NoViableAltException("", 19, 1, self.input)

                        raise nvae

                elif LA19 == 32:
                    alt19 = 2
                elif LA19 == 33:
                    LA19_3 = self.input.LA(2)

                    if (LA19_3 == DIGIT or LA19_3 == 31) :
                        alt19 = 5
                    elif (LA19_3 == EOF or LA19_3 == WHITESPACE or LA19_3 == DATA_BLOCK_HEADING) :
                        alt19 = 3
                    else:
                        nvae = NoViableAltException("", 19, 3, self.input)

                        raise nvae

                elif LA19 == CHAR_STRING:
                    alt19 = 4
                elif LA19 == DIGIT or LA19 == 34:
                    alt19 = 5
                elif LA19 == SEMI_COLON_TEXT_FIELD:
                    alt19 = 6
                else:
                    nvae = NoViableAltException("", 19, 0, self.input)

                    raise nvae

                if alt19 == 1:
                    # cif.g:79:10: inapplicable
                    pass
                    self._state.following.append(self.FOLLOW_inapplicable_in_value301)
                    self.inapplicable()

                    self._state.following.pop()


                elif alt19 == 2:
                    # cif.g:79:25: unknown
                    pass
                    self._state.following.append(self.FOLLOW_unknown_in_value305)
                    self.unknown()

                    self._state.following.pop()


                elif alt19 == 3:
                    # cif.g:79:35: '-'
                    pass
                    self.match(self.input, 33, self.FOLLOW_33_in_value309)


                elif alt19 == 4:
                    # cif.g:79:41: char_string
                    pass
                    self._state.following.append(self.FOLLOW_char_string_in_value313)
                    self.char_string()

                    self._state.following.pop()


                elif alt19 == 5:
                    # cif.g:79:56: numeric
                    pass
                    self._state.following.append(self.FOLLOW_numeric_in_value318)
                    self.numeric()

                    self._state.following.pop()


                elif alt19 == 6:
                    # cif.g:79:65: text_field
                    pass
                    self._state.following.append(self.FOLLOW_text_field_in_value321)
                    self.text_field()

                    self._state.following.pop()


                retval.stop = self.input.LT(-1)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return retval

    # $ANTLR end "value"


    # $ANTLR start "unsigned_integer"
    # cif.g:81:1: unsigned_integer : ( DIGIT )+ ;
    def unsigned_integer(self, ):

        try:
            try:
                # cif.g:82:2: ( ( DIGIT )+ )
                # cif.g:82:4: ( DIGIT )+
                pass
                # cif.g:82:4: ( DIGIT )+
                cnt20 = 0
                while True: #loop20
                    alt20 = 2
                    LA20_0 = self.input.LA(1)

                    if (LA20_0 == DIGIT) :
                        alt20 = 1


                    if alt20 == 1:
                        # cif.g:82:5: DIGIT
                        pass
                        self.match(self.input, DIGIT, self.FOLLOW_DIGIT_in_unsigned_integer332)


                    else:
                        if cnt20 >= 1:
                            break #loop20

                        eee = EarlyExitException(20, self.input)
                        raise eee

                    cnt20 += 1






            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "unsigned_integer"


    # $ANTLR start "integer"
    # cif.g:84:1: integer : ( '+' | '-' )? unsigned_integer ;
    def integer(self, ):

        try:
            try:
                # cif.g:84:9: ( ( '+' | '-' )? unsigned_integer )
                # cif.g:84:12: ( '+' | '-' )? unsigned_integer
                pass
                # cif.g:84:12: ( '+' | '-' )?
                alt21 = 2
                LA21_0 = self.input.LA(1)

                if ((33 <= LA21_0 <= 34)) :
                    alt21 = 1
                if alt21 == 1:
                    # cif.g:
                    pass
                    if (33 <= self.input.LA(1) <= 34):
                        self.input.consume()
                        self._state.errorRecovery = False

                    else:
                        mse = MismatchedSetException(None, self.input)
                        raise mse





                self._state.following.append(self.FOLLOW_unsigned_integer_in_integer355)
                self.unsigned_integer()

                self._state.following.pop()




            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "integer"


    # $ANTLR start "float_"
    # cif.g:86:1: float_ : ( integer EXPONENT | ( ( '+' | '-' )? ( ( DIGIT )* '.' unsigned_integer ) | ( DIGIT )+ '.' ) ( EXPONENT )? );
    def float_(self, ):

        try:
            try:
                # cif.g:86:8: ( integer EXPONENT | ( ( '+' | '-' )? ( ( DIGIT )* '.' unsigned_integer ) | ( DIGIT )+ '.' ) ( EXPONENT )? )
                alt27 = 2
                alt27 = self.dfa27.predict(self.input)
                if alt27 == 1:
                    # cif.g:86:11: integer EXPONENT
                    pass
                    self._state.following.append(self.FOLLOW_integer_in_float_365)
                    self.integer()

                    self._state.following.pop()
                    self.match(self.input, EXPONENT, self.FOLLOW_EXPONENT_in_float_367)


                elif alt27 == 2:
                    # cif.g:86:30: ( ( '+' | '-' )? ( ( DIGIT )* '.' unsigned_integer ) | ( DIGIT )+ '.' ) ( EXPONENT )?
                    pass
                    # cif.g:86:30: ( ( '+' | '-' )? ( ( DIGIT )* '.' unsigned_integer ) | ( DIGIT )+ '.' )
                    alt25 = 2
                    alt25 = self.dfa25.predict(self.input)
                    if alt25 == 1:
                        # cif.g:86:32: ( '+' | '-' )? ( ( DIGIT )* '.' unsigned_integer )
                        pass
                        # cif.g:86:32: ( '+' | '-' )?
                        alt22 = 2
                        LA22_0 = self.input.LA(1)

                        if ((33 <= LA22_0 <= 34)) :
                            alt22 = 1
                        if alt22 == 1:
                            # cif.g:
                            pass
                            if (33 <= self.input.LA(1) <= 34):
                                self.input.consume()
                                self._state.errorRecovery = False

                            else:
                                mse = MismatchedSetException(None, self.input)
                                raise mse





                        # cif.g:86:47: ( ( DIGIT )* '.' unsigned_integer )
                        # cif.g:86:49: ( DIGIT )* '.' unsigned_integer
                        pass
                        # cif.g:86:49: ( DIGIT )*
                        while True: #loop23
                            alt23 = 2
                            LA23_0 = self.input.LA(1)

                            if (LA23_0 == DIGIT) :
                                alt23 = 1


                            if alt23 == 1:
                                # cif.g:86:50: DIGIT
                                pass
                                self.match(self.input, DIGIT, self.FOLLOW_DIGIT_in_float_387)


                            else:
                                break #loop23


                        self.match(self.input, 31, self.FOLLOW_31_in_float_391)
                        self._state.following.append(self.FOLLOW_unsigned_integer_in_float_393)
                        self.unsigned_integer()

                        self._state.following.pop()





                    elif alt25 == 2:
                        # cif.g:86:82: ( DIGIT )+ '.'
                        pass
                        # cif.g:86:82: ( DIGIT )+
                        cnt24 = 0
                        while True: #loop24
                            alt24 = 2
                            LA24_0 = self.input.LA(1)

                            if (LA24_0 == DIGIT) :
                                alt24 = 1


                            if alt24 == 1:
                                # cif.g:86:83: DIGIT
                                pass
                                self.match(self.input, DIGIT, self.FOLLOW_DIGIT_in_float_399)


                            else:
                                if cnt24 >= 1:
                                    break #loop24

                                eee = EarlyExitException(24, self.input)
                                raise eee

                            cnt24 += 1


                        self.match(self.input, 31, self.FOLLOW_31_in_float_403)



                    # cif.g:86:97: ( EXPONENT )?
                    alt26 = 2
                    LA26_0 = self.input.LA(1)

                    if (LA26_0 == EXPONENT) :
                        alt26 = 1
                    if alt26 == 1:
                        # cif.g:86:98: EXPONENT
                        pass
                        self.match(self.input, EXPONENT, self.FOLLOW_EXPONENT_in_float_408)






            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "float_"


    # $ANTLR start "number"
    # cif.g:88:1: number : ( integer | float_ );
    def number(self, ):

        try:
            try:
                # cif.g:88:9: ( integer | float_ )
                alt28 = 2
                alt28 = self.dfa28.predict(self.input)
                if alt28 == 1:
                    # cif.g:88:11: integer
                    pass
                    self._state.following.append(self.FOLLOW_integer_in_number420)
                    self.integer()

                    self._state.following.pop()


                elif alt28 == 2:
                    # cif.g:88:21: float_
                    pass
                    self._state.following.append(self.FOLLOW_float__in_number424)
                    self.float_()

                    self._state.following.pop()



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "number"


    # $ANTLR start "numeric"
    # cif.g:90:1: numeric : ( number | ( number '(' ( DIGIT )+ ')' ) );
    def numeric(self, ):

        try:
            try:
                # cif.g:90:9: ( number | ( number '(' ( DIGIT )+ ')' ) )
                alt30 = 2
                alt30 = self.dfa30.predict(self.input)
                if alt30 == 1:
                    # cif.g:90:11: number
                    pass
                    self._state.following.append(self.FOLLOW_number_in_numeric433)
                    self.number()

                    self._state.following.pop()


                elif alt30 == 2:
                    # cif.g:90:20: ( number '(' ( DIGIT )+ ')' )
                    pass
                    # cif.g:90:20: ( number '(' ( DIGIT )+ ')' )
                    # cif.g:90:22: number '(' ( DIGIT )+ ')'
                    pass
                    self._state.following.append(self.FOLLOW_number_in_numeric439)
                    self.number()

                    self._state.following.pop()
                    self.match(self.input, 35, self.FOLLOW_35_in_numeric441)
                    # cif.g:90:33: ( DIGIT )+
                    cnt29 = 0
                    while True: #loop29
                        alt29 = 2
                        LA29_0 = self.input.LA(1)

                        if (LA29_0 == DIGIT) :
                            alt29 = 1


                        if alt29 == 1:
                            # cif.g:90:34: DIGIT
                            pass
                            self.match(self.input, DIGIT, self.FOLLOW_DIGIT_in_numeric444)


                        else:
                            if cnt29 >= 1:
                                break #loop29

                            eee = EarlyExitException(29, self.input)
                            raise eee

                        cnt29 += 1


                    self.match(self.input, 36, self.FOLLOW_36_in_numeric448)






            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "numeric"


    # $ANTLR start "char_string"
    # cif.g:92:1: char_string : CHAR_STRING ;
    def char_string(self, ):

        try:
            try:
                # cif.g:93:2: ( CHAR_STRING )
                # cif.g:93:4: CHAR_STRING
                pass
                self.match(self.input, CHAR_STRING, self.FOLLOW_CHAR_STRING_in_char_string460)




            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "char_string"


    # $ANTLR start "text_field"
    # cif.g:95:1: text_field : SEMI_COLON_TEXT_FIELD ;
    def text_field(self, ):

        try:
            try:
                # cif.g:96:2: ( SEMI_COLON_TEXT_FIELD )
                # cif.g:96:4: SEMI_COLON_TEXT_FIELD
                pass
                self.match(self.input, SEMI_COLON_TEXT_FIELD, self.FOLLOW_SEMI_COLON_TEXT_FIELD_in_text_field470)




            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
        finally:

            pass

        return

    # $ANTLR end "text_field"


    # Delegated rules


    # lookup tables for DFA #8

    DFA8_eot = DFA.unpack(
        u"\5\uffff"
        )

    DFA8_eof = DFA.unpack(
        u"\2\2\3\uffff"
        )

    DFA8_min = DFA.unpack(
        u"\2\5\1\uffff\1\5\1\uffff"
        )

    DFA8_max = DFA.unpack(
        u"\1\11\1\42\1\uffff\1\42\1\uffff"
        )

    DFA8_accept = DFA.unpack(
        u"\2\uffff\1\2\1\uffff\1\1"
        )

    DFA8_special = DFA.unpack(
        u"\5\uffff"
        )


    DFA8_transition = [
        DFA.unpack(u"\1\1\3\uffff\1\2"),
        DFA.unpack(u"\1\3\5\2\1\4\1\uffff\2\4\20\uffff\4\4"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\3\5\2\1\4\1\uffff\2\4\20\uffff\4\4"),
        DFA.unpack(u"")
    ]

    # class definition for DFA #8

    DFA8 = DFA
    # lookup tables for DFA #10

    DFA10_eot = DFA.unpack(
        u"\4\uffff"
        )

    DFA10_eof = DFA.unpack(
        u"\4\uffff"
        )

    DFA10_min = DFA.unpack(
        u"\2\5\2\uffff"
        )

    DFA10_max = DFA.unpack(
        u"\1\5\1\12\2\uffff"
        )

    DFA10_accept = DFA.unpack(
        u"\2\uffff\1\1\1\2"
        )

    DFA10_special = DFA.unpack(
        u"\4\uffff"
        )


    DFA10_transition = [
        DFA.unpack(u"\1\1"),
        DFA.unpack(u"\1\1\1\uffff\1\3\1\2\1\uffff\1\2"),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]

    # class definition for DFA #10

    DFA10 = DFA
    # lookup tables for DFA #16

    DFA16_eot = DFA.unpack(
        u"\5\uffff"
        )

    DFA16_eof = DFA.unpack(
        u"\2\2\3\uffff"
        )

    DFA16_min = DFA.unpack(
        u"\2\5\2\uffff\1\5"
        )

    DFA16_max = DFA.unpack(
        u"\1\11\1\12\2\uffff\1\12"
        )

    DFA16_accept = DFA.unpack(
        u"\2\uffff\1\2\1\1\1\uffff"
        )

    DFA16_special = DFA.unpack(
        u"\5\uffff"
        )


    DFA16_transition = [
        DFA.unpack(u"\1\1\3\uffff\1\2"),
        DFA.unpack(u"\1\4\1\3\1\uffff\1\3\1\2\1\3"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\4\1\3\1\uffff\1\3\1\2\1\3")
    ]

    # class definition for DFA #16

    DFA16 = DFA
    # lookup tables for DFA #18

    DFA18_eot = DFA.unpack(
        u"\5\uffff"
        )

    DFA18_eof = DFA.unpack(
        u"\5\uffff"
        )

    DFA18_min = DFA.unpack(
        u"\3\5\2\uffff"
        )

    DFA18_max = DFA.unpack(
        u"\1\5\2\42\2\uffff"
        )

    DFA18_accept = DFA.unpack(
        u"\3\uffff\1\2\1\1"
        )

    DFA18_special = DFA.unpack(
        u"\5\uffff"
        )


    DFA18_transition = [
        DFA.unpack(u"\1\1"),
        DFA.unpack(u"\1\2\2\uffff\1\4\2\uffff\1\3\1\uffff\2\3\20\uffff"
        u"\4\3"),
        DFA.unpack(u"\1\2\2\uffff\1\4\2\uffff\1\3\1\uffff\2\3\20\uffff"
        u"\4\3"),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]

    # class definition for DFA #18

    DFA18 = DFA
    # lookup tables for DFA #27

    DFA27_eot = DFA.unpack(
        u"\6\uffff"
        )

    DFA27_eof = DFA.unpack(
        u"\6\uffff"
        )

    DFA27_min = DFA.unpack(
        u"\3\13\1\uffff\1\13\1\uffff"
        )

    DFA27_max = DFA.unpack(
        u"\1\42\2\37\1\uffff\1\37\1\uffff"
        )

    DFA27_accept = DFA.unpack(
        u"\3\uffff\1\2\1\uffff\1\1"
        )

    DFA27_special = DFA.unpack(
        u"\6\uffff"
        )


    DFA27_transition = [
        DFA.unpack(u"\1\2\23\uffff\1\3\1\uffff\2\1"),
        DFA.unpack(u"\1\4\23\uffff\1\3"),
        DFA.unpack(u"\1\2\1\5\22\uffff\1\3"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\4\1\5\22\uffff\1\3"),
        DFA.unpack(u"")
    ]

    # class definition for DFA #27

    DFA27 = DFA
    # lookup tables for DFA #25

    DFA25_eot = DFA.unpack(
        u"\5\uffff"
        )

    DFA25_eof = DFA.unpack(
        u"\3\uffff\1\4\1\uffff"
        )

    DFA25_min = DFA.unpack(
        u"\1\13\1\uffff\1\13\1\5\1\uffff"
        )

    DFA25_max = DFA.unpack(
        u"\1\42\1\uffff\1\37\1\43\1\uffff"
        )

    DFA25_accept = DFA.unpack(
        u"\1\uffff\1\1\2\uffff\1\2"
        )

    DFA25_special = DFA.unpack(
        u"\5\uffff"
        )


    DFA25_transition = [
        DFA.unpack(u"\1\2\23\uffff\1\1\1\uffff\2\1"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\2\23\uffff\1\3"),
        DFA.unpack(u"\1\4\3\uffff\1\4\1\uffff\1\1\1\4\26\uffff\1\4"),
        DFA.unpack(u"")
    ]

    # class definition for DFA #25

    DFA25 = DFA
    # lookup tables for DFA #28

    DFA28_eot = DFA.unpack(
        u"\6\uffff"
        )

    DFA28_eof = DFA.unpack(
        u"\2\uffff\1\5\1\uffff\1\5\1\uffff"
        )

    DFA28_min = DFA.unpack(
        u"\2\13\1\5\1\uffff\1\5\1\uffff"
        )

    DFA28_max = DFA.unpack(
        u"\1\42\1\37\1\43\1\uffff\1\43\1\uffff"
        )

    DFA28_accept = DFA.unpack(
        u"\3\uffff\1\2\1\uffff\1\1"
        )

    DFA28_special = DFA.unpack(
        u"\6\uffff"
        )


    DFA28_transition = [
        DFA.unpack(u"\1\2\23\uffff\1\3\1\uffff\2\1"),
        DFA.unpack(u"\1\4\23\uffff\1\3"),
        DFA.unpack(u"\1\5\3\uffff\1\5\1\uffff\1\2\1\3\22\uffff\1\3\3\uffff"
        u"\1\5"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\5\3\uffff\1\5\1\uffff\1\4\1\3\22\uffff\1\3\3\uffff"
        u"\1\5"),
        DFA.unpack(u"")
    ]

    # class definition for DFA #28

    DFA28 = DFA
    # lookup tables for DFA #30

    DFA30_eot = DFA.unpack(
        u"\13\uffff"
        )

    DFA30_eof = DFA.unpack(
        u"\2\uffff\1\10\1\uffff\3\10\2\uffff\2\10"
        )

    DFA30_min = DFA.unpack(
        u"\2\13\1\5\1\13\3\5\2\uffff\2\5"
        )

    DFA30_max = DFA.unpack(
        u"\1\42\1\37\1\43\1\13\3\43\2\uffff\2\43"
        )

    DFA30_accept = DFA.unpack(
        u"\7\uffff\1\2\1\1\2\uffff"
        )

    DFA30_special = DFA.unpack(
        u"\13\uffff"
        )


    DFA30_transition = [
        DFA.unpack(u"\1\2\23\uffff\1\3\1\uffff\2\1"),
        DFA.unpack(u"\1\4\23\uffff\1\3"),
        DFA.unpack(u"\1\10\3\uffff\1\10\1\uffff\1\2\1\5\22\uffff\1\6\3"
        u"\uffff\1\7"),
        DFA.unpack(u"\1\11"),
        DFA.unpack(u"\1\10\3\uffff\1\10\1\uffff\1\4\1\5\22\uffff\1\3\3"
        u"\uffff\1\7"),
        DFA.unpack(u"\1\10\3\uffff\1\10\31\uffff\1\7"),
        DFA.unpack(u"\1\10\3\uffff\1\10\1\uffff\1\11\1\12\26\uffff\1\7"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\10\3\uffff\1\10\1\uffff\1\11\1\12\26\uffff\1\7"),
        DFA.unpack(u"\1\10\3\uffff\1\10\31\uffff\1\7")
    ]

    # class definition for DFA #30

    DFA30 = DFA


    FOLLOW_cif_in_parse44 = frozenset([1])
    FOLLOW_COMMENTS_in_cif57 = frozenset([5, 9])
    FOLLOW_WHITESPACE_in_cif62 = frozenset([5, 9])
    FOLLOW_data_block_in_cif68 = frozenset([5, 9])
    FOLLOW_WHITESPACE_in_cif72 = frozenset([5, 9])
    FOLLOW_data_block_in_cif75 = frozenset([5, 9])
    FOLLOW_WHITESPACE_in_cif81 = frozenset([])
    FOLLOW_EOF_in_cif88 = frozenset([1])
    FOLLOW_value_in_loop_body106 = frozenset([1, 5])
    FOLLOW_WHITESPACE_in_loop_body119 = frozenset([5, 11, 13, 14, 31, 32, 33, 34])
    FOLLOW_value_in_loop_body133 = frozenset([1, 5])
    FOLLOW_SAVE_FRAME_HEADING_in_save_frame157 = frozenset([5])
    FOLLOW_WHITESPACE_in_save_frame161 = frozenset([5, 8, 10])
    FOLLOW_data_items_in_save_frame164 = frozenset([5])
    FOLLOW_WHITESPACE_in_save_frame169 = frozenset([5, 7])
    FOLLOW_SAVE_in_save_frame172 = frozenset([1])
    FOLLOW_TAG_in_data_items182 = frozenset([5])
    FOLLOW_WHITESPACE_in_data_items184 = frozenset([11, 13, 14, 31, 32, 33, 34])
    FOLLOW_value_in_data_items186 = frozenset([1])
    FOLLOW_loop_header_in_data_items199 = frozenset([5, 11, 13, 14, 31, 32, 33, 34])
    FOLLOW_WHITESPACE_in_data_items201 = frozenset([5, 11, 13, 14, 31, 32, 33, 34])
    FOLLOW_loop_body_in_data_items204 = frozenset([1])
    FOLLOW_DATA_BLOCK_HEADING_in_data_block217 = frozenset([1, 5])
    FOLLOW_WHITESPACE_in_data_block230 = frozenset([5, 6, 8, 10])
    FOLLOW_data_items_in_data_block235 = frozenset([1, 5])
    FOLLOW_save_frame_in_data_block239 = frozenset([1, 5])
    FOLLOW_LOOP__in_loop_header255 = frozenset([5])
    FOLLOW_WHITESPACE_in_loop_header259 = frozenset([5, 8])
    FOLLOW_TAG_in_loop_header262 = frozenset([5])
    FOLLOW_WHITESPACE_in_loop_header267 = frozenset([1])
    FOLLOW_31_in_inapplicable282 = frozenset([1])
    FOLLOW_32_in_unknown291 = frozenset([1])
    FOLLOW_inapplicable_in_value301 = frozenset([1])
    FOLLOW_unknown_in_value305 = frozenset([1])
    FOLLOW_33_in_value309 = frozenset([1])
    FOLLOW_char_string_in_value313 = frozenset([1])
    FOLLOW_numeric_in_value318 = frozenset([1])
    FOLLOW_text_field_in_value321 = frozenset([1])
    FOLLOW_DIGIT_in_unsigned_integer332 = frozenset([1, 11])
    FOLLOW_set_in_integer344 = frozenset([11, 33, 34])
    FOLLOW_unsigned_integer_in_integer355 = frozenset([1])
    FOLLOW_integer_in_float_365 = frozenset([12])
    FOLLOW_EXPONENT_in_float_367 = frozenset([1])
    FOLLOW_set_in_float_373 = frozenset([11, 31])
    FOLLOW_DIGIT_in_float_387 = frozenset([11, 31])
    FOLLOW_31_in_float_391 = frozenset([11, 33, 34])
    FOLLOW_unsigned_integer_in_float_393 = frozenset([1, 12])
    FOLLOW_DIGIT_in_float_399 = frozenset([11, 31])
    FOLLOW_31_in_float_403 = frozenset([1, 12])
    FOLLOW_EXPONENT_in_float_408 = frozenset([1])
    FOLLOW_integer_in_number420 = frozenset([1])
    FOLLOW_float__in_number424 = frozenset([1])
    FOLLOW_number_in_numeric433 = frozenset([1])
    FOLLOW_number_in_numeric439 = frozenset([35])
    FOLLOW_35_in_numeric441 = frozenset([11])
    FOLLOW_DIGIT_in_numeric444 = frozenset([11, 36])
    FOLLOW_36_in_numeric448 = frozenset([1])
    FOLLOW_CHAR_STRING_in_char_string460 = frozenset([1])
    FOLLOW_SEMI_COLON_TEXT_FIELD_in_text_field470 = frozenset([1])



def main(argv, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    from antlr3.main import ParserMain
    main = ParserMain("cifLexer", cifParser)
    main.stdin = stdin
    main.stdout = stdout
    main.stderr = stderr
    main.execute(argv)


if __name__ == '__main__':
    main(sys.argv)

#ifndef _ANTLR3_FILESTREAM_H
#define _ANTLR3_FILESTREAM_H

// [The "BSD licence"]
// Copyright (c) 2005-2009 Jim Idle, Temporal Wave LLC
// http://www.temporal-wave.com
// http://www.linkedin.com/in/jimidle
//
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions
// are met:
// 1. Redistributions of source code must retain the above copyright
//    notice, this list of conditions and the following disclaimer.
// 2. Redistributions in binary form must reproduce the above copyright
//    notice, this list of conditions and the following disclaimer in the
//    documentation and/or other materials provided with the distribution.
// 3. The name of the author may not be used to endorse or promote products
//    derived from this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
// IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
// OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
// IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
// INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
// NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
// THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
// THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#include    <antlr3defs.h>

#ifdef __cplusplus
extern "C" {
#endif

ANTLR3_API ANTLR3_FDSC  antlr3Fopen     (pANTLR3_UINT8 filename, const char * mode);
ANTLR3_API void         antlr3Fclose    (ANTLR3_FDSC fd);

ANTLR3_API ANTLR3_UINT32        antlr3Fsize     (pANTLR3_UINT8 filename);
ANTLR3_API ANTLR3_UINT32        antlr3readAscii (pANTLR3_INPUT_STREAM input, pANTLR3_UINT8 fileName);
ANTLR3_API ANTLR3_UINT32        antlr3Fread     (ANTLR3_FDSC fdsc, ANTLR3_UINT32 count,  void * data);

#ifdef __cplusplus
}
#endif

#endif

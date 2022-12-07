# Logging ANSI Handler

This document details the Ansi Handler

## How to Use

```python
from edk2toollib.logging.ansi_handler import ColoredStreamHandler

handler = ColoredStreamHandler(stream, strip=True, convert=False)
formatter = ColoredFormatter()
```

## Usage info

ColoredStreamHandler() will create a handler from the logging package. It
accepts a stream (such as a file) and will display the colors in that particular
stream as needed to the console. There are two options, strip and convert.

ColoredFormatter() will create a formatter from the logging package that will
insert ANSI codes according to the logging level into the output stream.

### ColoredStreamHandler Arguments

### 1. strip

Strip will strip ANSI codes if the terminal does not support them (such as
windows).

### 2. convert

Convert will convert ANSI codes on windows platforms into windows platform
calls.

### ColoredFormatter Arguments

### 1. msg

The best documentation for this is from Python itself. It's the same message
that's passed into the formatted base class.

### 2. use_azure

Azure Dev ops can support colors with certain keywords. This turns that on
instead of using ANSI.

## Purpose

  To put color into your life and your terminal, we needed to support coloring
  based on logging levels. ANSI seemed like a universal choice. The
  StreamHandler is just a workaround for windows based systems that don't
  support ANSI natively.

load-display pandagl
win-origin 150 50
win-size 800 600
fullscreen #f
framebuffer-hardware #t
framebuffer-software #f

# These set the minimum requirements for the framebuffer.

depth-bits 16
color-bits 16
alpha-bits 0
stencil-bits 0
multisamples 0

# These control the amount of output Panda gives for some various
# categories.  The severity levels, in order, are "spam", "debug",
# "info", "warning", and "fatal"; the default is "info".  Uncomment
# one (or define a new one for the particular category you wish to
# change) to control this output.

notify-level warning
default-directnotify-level warning

# These specify where model files may be loaded from.  You probably
# want to set this to a sensible path for yourself.  $THIS_PRC_DIR is
# a special variable that indicates the same directory as this
# particular Config.prc file.

model-path    $THIS_PRC_DIR
model-path    $THIS_PRC_DIR/scene.mf
sound-path    $THIS_PRC_DIR
texture-path  $THIS_PRC_DIR/scene.mf
texture-path  $THIS_PRC_DIR


want-directtools  f
want-tk           f

# Enable/disable performance profiling tool and frame-rate meter

want-pstats            f
show-frame-rate-meter  t

# Audio
audio-library-name p3openal_audio
audio-buffering-seconds 1.0
audio-cache-limit 15    
audio-play-mp3 f

# Enable the use of the new movietexture class.
use-movietexture #t

# The new version of panda supports hardware vertex animation, but it's not quite ready
hardware-animated-vertices 0

# Enable the model-cache
# model-cache-dir /usr/share/panda3d/modelcache
# model-cache-textures #t

# Limit the use of advanced shader profiles.
# Currently, advanced profiles are not reliable under Cg.
basic-shaders-only #t

# OTHERS

# forget about v-sync
sync-video 0

# trigger a core dump on first assertion
assert-abort 1
#notify-output filename
#plugin-path search-path

#egg-suppress-hidden 1
#icon-filename

#lock-to-one-cpu f
vertex-data-compression-level 3
 

# if video card is intel, set it to false
# in general put all video card related config in a different config file
auto-generate-mipmaps t 
compressed-textures t

# Available only in 1.6
#model-cache-dir /c/temp/panda-cache
#model-cache-compressed-textures 1


window-type none
text-encoding utf8


# CUSTOM
lang fr_FR
# HW REQUIREMENTS
required-ram 128
required-space 102400

# VIDEO
load-display pandagl
win-size 800 600
win-origin 400 0
fullscreen #f
framebuffer-hardware #t
framebuffer-software #f
basic-shaders-only #t
sync-video 0
vertex-data-compression-level 3
window-type none
auto-generate-mipmaps t 
compressed-textures t
depth-bits 16
color-bits 16
alpha-bits 0
stencil-bits 0
multisamples 0


# LOGGING
notify-level error
default-directnotify-level warning

# PATHS
model-path    $THIS_PRC_DIR
model-path    $THIS_PRC_DIR/scene.mf
model-path    $THIS_PRC_DIR/gui
model-path    $THIS_PRC_DIR/fonts
sound-path    $THIS_PRC_DIR
texture-path  $THIS_PRC_DIR
texture-path  $THIS_PRC_DIR/scene.mf
texture-path  $THIS_PRC_DIR/gui
texture-path  $THIS_PRC_DIR/fonts
track-def-path $THIS_PRC_DIR/tracks/tracks.bin

# DEBUG
want-directtools  #t
want-tk           #t
want-pstats            #f
show-frame-rate-meter  #t
# trigger a core dump on first assertion
assert-abort 1
cap-framerate 1
direct-gui-edit #t

# AUDIO
audio-library-name p3openal_audio
audio-buffering-seconds 1.0
audio-cache-limit 15    
audio-play-mp3 f

# CACHE, available only in 1.6
#model-cache-dir $THIS_PRC_DIR/cache
#model-cache-textures #t
#model-cache-compressed-textures 1

# LANGUAGE
lang fr_FR
text-encoding utf8

# OTHERS
#egg-suppress-hidden 1
#icon-filename
#lock-to-one-cpu f

# default font
text-default-font astronbo.ttf
 
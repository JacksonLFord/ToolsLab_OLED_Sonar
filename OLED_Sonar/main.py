from machine import Pin, I2C
from utime import sleep, ticks_ms, ticks_diff

# --- I2C Setup ---
# I2C bus 1 using GP26 as SDA and GP27 as SCL at 400kHz (fast mode)
i2c = I2C(1, sda=Pin(26), scl=Pin(27), freq=400000)

# Scan the I2C bus for connected devices and print their addresses
devices = i2c.scan()
print("I2C devices found:", [hex(d) for d in devices])

if not devices:
    # No devices were detected — print an error and wiring checklist to help debug
    print()
    print("ERROR: No I2C devices detected!")
    print()
    print("Troubleshooting checklist:")
    print("  1. Check wiring:")
    print("     VCC -> 3V3 (pin 36)")
    print("     GND -> GND (pin 38)")
    print("     SDA -> GP26 (pin 31)")
    print("     SCL -> GP27 (pin 32)")
    print("  2. Make sure connections are solid (not loose)")
    print("  3. Some displays use 5V, try VCC -> VBUS (pin 40)")
    print("  4. Check if SDA/SCL labels are swapped on your board")

else:
    # At least one I2C device was found — proceed with display setup
    from sh1106 import SH1106_I2C

    # Use the first detected device address (should be 0x3C for most SH1106 displays)
    addr = devices[0]
    print("Using device at address:", hex(addr))

    # Initialize the SH1106 OLED display: 128px wide, 64px tall, over I2C
    oled = SH1106_I2C(128, 64, i2c, addr=addr)

    # --- Test Screen 1: Connection confirmation ---
    # This verifies the display is working before moving to the animation
    oled.fill(0)                           # Clear the screen (fill with black)
    oled.text("Hello!", 0, 0)              # Line 1: greeting
    oled.text("Pico 2W + SH1106", 0, 16)  # Line 2: hardware info
    oled.text("I2C LCD Ready", 0, 32)      # Line 3: status
    oled.show()                            # Push the frame buffer to the display
    sleep(5)                               # Hold the test screen for 5 seconds

    # --- Test Screen 2: Custom message ---
    oled.fill(0)                           # Clear the screen
    oled.text("This is my code!", 0, 0)    # Line 1: personal label
    oled.text("I hate physics", 0, 16)     # Line 2: relatable message
    oled.show()
    sleep(5)                               # Hold for 5 seconds before starting animation

    # --- Clear screen before animation begins ---
    oled.fill(0)

    # --- Helper function: Draw a filled circle ---
    # The built-in framebuf only supports outlines, so we draw it manually
    # by stacking horizontal lines (hline) from top to bottom of the circle.
    # cx, cy = centre coordinates; r = radius; col = colour (1=white, 0=black)
    def fill_circle(oled, cx, cy, r, col=1):
        for dy in range(-r, r + 1):
            # Pythagorean theorem: dx = sqrt(r² - dy²) gives the half-width at each row
            dx = int((r * r - dy * dy) ** 0.5)
            oled.hline(cx - dx, cy + dy, dx * 2 + 1, col)

    # --- Animation constants ---
    SCREEN_W    = 128   # Display width in pixels
    SCREEN_H    = 64    # Display height in pixels
    BALL_R      = 5     # Ball radius in pixels

    # --- Ball initial state ---
    bx = 20   # Ball centre X position (pixels from left)
    by = 20   # Ball centre Y position (pixels from top)
    vx = 2    # Horizontal velocity (pixels per frame, positive = moving right)
    vy = 2    # Vertical velocity (pixels per frame, positive = moving down)

    # --- Scrolling text state ---
    scroll_msg   = "  ** PHYSICS IS HARD **  "  # Message to scroll across the bottom
    scroll_x     = SCREEN_W   # Start off-screen to the right so it scrolls in
    TEXT_Y       = 52         # Y position of the scrolling text (near the bottom)
    SCROLL_SPEED = 2          # How many pixels the text moves left each frame

    # --- Animation timing ---
    # Record the start time in milliseconds so we can run for exactly 15 seconds
    start  = ticks_ms()
    RUN_MS = 15_000   # Total animation duration: 15,000 ms = 15 seconds

    frame = 0  # Frame counter (used for debugging / tracking progress)

    # --- Main animation loop ---
    # ticks_diff(now, start) gives elapsed ms; loop runs until 15 seconds have passed
    while ticks_diff(ticks_ms(), start) < RUN_MS:
        oled.fill(0)  # Clear the screen at the start of every frame

        # --- Element 1: Bouncing Ball ---
        # Update ball position by adding velocity each frame
        bx += vx
        by += vy

        # Bounce off the LEFT wall: if the left edge of the ball hits x=0, reverse horizontal direction
        if bx - BALL_R <= 0:
            bx = BALL_R       # Clamp position so the ball doesn't go out of bounds
            vx = abs(vx)      # Force velocity to be positive (moving right)

        # Bounce off the RIGHT wall
        elif bx + BALL_R >= SCREEN_W - 1:
            bx = SCREEN_W - 1 - BALL_R   # Clamp to right edge
            vx = -abs(vx)                 # Force velocity to be negative (moving left)

        # Bounce off the TOP wall
        if by - BALL_R <= 0:
            by = BALL_R       # Clamp to top edge
            vy = abs(vy)      # Force velocity downward

        # Bounce off the BOTTOM boundary (kept above the scrolling text area)
        elif by + BALL_R >= TEXT_Y - 2:
            by = TEXT_Y - 2 - BALL_R   # Clamp so ball stays above the divider line
            vy = -abs(vy)              # Force velocity upward

        # Draw the ball at its new position
        fill_circle(oled, bx, by, BALL_R, 1)

        # --- Element 2: Scrolling Text ---
        # Draw the text at its current horizontal position
        oled.text(scroll_msg, scroll_x, TEXT_Y)

        # Move the text left by SCROLL_SPEED pixels each frame
        scroll_x -= SCROLL_SPEED

        # Once the entire message has scrolled off the left edge, reset it to start again from the right
        msg_px = len(scroll_msg) * 8   # Each character is 8 pixels wide
        if scroll_x < -msg_px:
            scroll_x = SCREEN_W        # Reset to the right edge for a seamless loop

        # --- Divider line ---
        # Draw a horizontal line separating the ball area from the scrolling text
        oled.hline(0, TEXT_Y - 4, SCREEN_W, 1)

        # Push the completed frame to the display
        oled.show()

        frame += 1      # Increment frame counter
        sleep(0.04)     # Wait ~40ms per frame → approximately 25 frames per second

    # --- Animation complete ---
    oled.fill(0)
    oled.text("Done! :)", 32, 24)   # Display a finished message centred on screen
    oled.show()
    print("Display initialized!")
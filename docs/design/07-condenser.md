## 7. Condenser / iris assembly

Committed optical parts:

- Thorlabs ACL2520U-A condenser
- Thorlabs SM1V05 adjustable lens cell
- Thorlabs SM1L03 tube
- Thorlabs SM1D12 adjustable iris
- Thorlabs SMR1/M fixed threaded holder
- Thorlabs SM1CP1 internally threaded protective cap
- Thorlabs SM1EC2 protective cap
- TR50/M post + common rail shoe

### 7.1 Stack order

From the LED to the slit:

1. threaded LED module (§6.5), its SM1CP2M cap threaded into the LED-side face of the SMR1/M;
2. SMR1/M on the TR50/M (0.400 in / 10.16 mm thick, SM1 thread through, no lip; 0.870 in / 22.10 mm
   post-top-to-axis offset);
3. SM1V05, its externally threaded sleeve entering the slit-side face of the SMR1/M and locked with the
   included SM1NT. The ACL2520U-A sits in the SM1V05 body with its plano face on the internal seat (toward
   the LED) and its convex face toward the open end;
4. SM1L03, threaded into the SM1V05 open end;
5. SM1D12, threaded into the SM1L03.

The ACL2520U-A convex vertex sits about 0.7 mm inside the SM1V05 open end, so the SM1L03 spacer is required
ahead of the iris; the SM1D12 interferes with the lens if threaded directly into the SM1V05.

The cap and the SM1V05 sleeve share the SMR1/M thread. SM1V05 engagement runs from the Thorlabs minimum of
0.110 in / 2.79 mm to about 5.7–5.8 mm, where the sleeve end comes within 0.3 mm of the LED board. Turning
the SM1V05 moves the lens, SM1L03, and iris together relative to the LED; the resulting few-millimeter iris
shift is negligible against the 150 mm iris-to-slit spacing.

### 7.2 Condenser optics

The condenser images the LED emitter onto the source slit (about 6.6× magnification). Each slit point then
sees the iris uniformly filled at the LED radiance, which gives a uniformly illuminated mirror. The LED image
should cover the illuminated slit length; the domes enlarge the apparent emitters by about 1.4–1.5×.

Defocus in either direction underfills the ±1.8° cone: iris-edge rays then trace back beyond the emitter
edge, darkening the mirror edge and shortening the uniformly lit slit length. With the LED at the condenser
focus (12 mm, collimated) the emitter cannot fill the cone even at the slit center.

Using ACL2520U-A catalog values (EFL 20.1 mm, BFL 12.0 mm; object-side principal plane about 8.1 mm inside
the plano face) and about 153 mm from the convex vertex to the slit, the optimum emitter-to-plano-face gap is
about 15 mm. The optimum moves only about ±0.7 mm for ±30 mm of slit position.

### 7.3 Setup values

- emitter-to-plano-face gap approximately 15 mm, measured to the emitting surface, not the dome top
- useful gap range roughly 13–17 mm
- condenser/iris-to-slit spacing approximately 150 mm
- initial iris opening approximately 9–10.5 mm (about ±1.7–2.0° at 150 mm)

Set focus by imaging the LED onto the closed slit blades and turning the SM1V05 until the emitter image is
sharp and centered, then lock the SM1NT and open the slit. These are setup values, not hard CAD dimensions.

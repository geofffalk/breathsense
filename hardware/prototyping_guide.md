# Septum Ring Prototyping: Gold Contact Pads

## Overview
3D print the ring body, then add conductive contact pads for the detachable connection.

---

## Method 1: Copper Tape + Gold Plating Pen (Easiest)

### Materials
- 3D printed ring (PLA/resin)
- **Copper tape** (adhesive-backed, from Amazon/eBay)
- **Conductive gold paint pen** (optional, for corrosion resistance)
- Thin magnet wire for internal routing

### Steps
1. **Print ring** with two small flat areas (~2×2mm) on the ball end
2. **Cut copper tape** into 2×2mm squares
3. **Stick tape** onto flat areas
4. **Route wire** through ring body to each pad
5. **Solder** magnet wire to back of copper tape
6. **Optional**: Paint over copper with gold pen for skin-safe finish

---

## Method 2: Embedded Brass Inserts (More Durable)

### Materials
- 3D printed ring with **1.5mm holes** in ball end
- **Brass rod** (1.5mm diameter) or brass rivets
- Solder + flux

### Steps
1. **Print ring** with two 1.5mm holes where pads should be
2. **Cut brass rod** into 2mm lengths
3. **Press-fit** brass pieces into holes (friction fit)
4. **File flush** with ball surface
5. **Solder** wires to back of brass inserts

---

## Method 3: Conductive Filament Pads (All-in-One)

### Materials
- Standard PLA filament
- **Conductive PLA** (carbon or copper-filled)
- Dual-extruder printer OR manual filament swap

### Steps
1. **Print ring** with pause at pad layer
2. **Swap to conductive filament** for pad area
3. **Resume print** with standard filament
4. Conductive pads are now integral to the print

---

## Spring Clip Connector (Chain Side)

```
     ┌─────────────────┐
     │   Spring Clip   │
     │  ┌───┐   ┌───┐  │
     │  │ ◉ │   │ ◉ │  │ ← Contact leaves
     │  └─┬─┘   └─┬─┘  │
     │    │       │    │
     │  Wire to XIAO   │
     └─────────────────┘
         Clips onto
      ring bar/ball end
```

Use thin **phosphor bronze** or **beryllium copper** sheet (0.1-0.2mm) to make spring contacts.

---

## Where to Buy

| Item | UK Source |
|------|-----------|
| Copper tape (5mm wide) | Amazon UK, eBay |
| Gold conductive pen | RS Components, Amazon |
| Brass rod 1.5mm | Hobbycraft, model shops |
| Phosphor bronze sheet | eBay, metals4u.co.uk |
| Conductive PLA | Amazon UK, 3DFilaprint |

---

## Recommended First Prototype

1. Print ring with flat pads on ball (see OpenSCAD below)
2. Use **copper tape + solder** approach
3. Test continuity with multimeter
4. Attach thermistor wires

Simple, fast, and easy to iterate.

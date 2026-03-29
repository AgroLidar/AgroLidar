# Tractor STL assets

Primary runtime tractor mesh:
- `John_Deere_6195M_primary.stl`

Source upload expected from product team:
- `John_Deere_6195M ( Z 156.3 - Y 108 - X 83.25 ) mm.stl`

Normalization performed at runtime in `TractorVehicle.tsx`:
- centered pivot
- normalized scale to simulator wheelbase
- face-normal cleanup + welded vertices for browser rendering

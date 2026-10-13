with Tracks; use Tracks;

--  Restricted zones: rectangles in sensor coordinates (metres).
package Zones is

   function In_Restricted_Zone (P : Position) return Boolean;

end Zones;

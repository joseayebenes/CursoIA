with Ada.Real_Time; use Ada.Real_Time;

package body Clocks is

   Start : constant Time := Ada.Real_Time.Clock;

   function Now return Tracks.Seconds is
   begin
      return Tracks.Seconds (To_Duration (Ada.Real_Time.Clock - Start));
   end Now;

end Clocks;

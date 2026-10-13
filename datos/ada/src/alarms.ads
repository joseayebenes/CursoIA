with Tracks; use Tracks;

--  Alarms raised when a track enters a restricted zone.
package Alarms is

   procedure Check (T : Track);
   --  Raises an alarm if T has just entered a restricted zone.

end Alarms;

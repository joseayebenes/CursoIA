with Tracks;

--  The time base of the software.
package Clocks is

   function Now return Tracks.Seconds;
   --  Time since the software started.

end Clocks;

with Tracks; use Tracks;

--  Reports from the primary sensor. This version reads them from standard
--  input, one per line: target number, X and Y in metres.
package Sensor_Input is

   type Report is record
      Target : Positive := 1;
      Pos    : Position;
   end record;

   procedure Read (R : out Report; Available : out Boolean);
   --  The next report. Available is False when the sensor has stopped.

end Sensor_Input;

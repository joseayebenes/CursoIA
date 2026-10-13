with Ada.Text_IO;
with Clocks;

package body Logger is

   --  Req: SRS-0008, SRS-0009
   procedure Log (Message : String) is
   begin
      Ada.Text_IO.Put_Line
        ("[" & Duration'Image (Duration (Clocks.Now)) & " s] " & Message);
   end Log;

end Logger;

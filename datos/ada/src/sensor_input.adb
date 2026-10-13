with Ada.Text_IO;
with Ada.Integer_Text_IO;
with Ada.Float_Text_IO;

package body Sensor_Input is

   --  Req: SRS-0001
   procedure Read (R : out Report; Available : out Boolean) is
      Target : Integer;
      X, Y   : Float;
      Last   : Natural;
   begin
      if Ada.Text_IO.End_Of_File then
         R := (Target => 1, Pos => (0.0, 0.0));
         Available := False;
         return;
      end if;
      declare
         Line : constant String := Ada.Text_IO.Get_Line;
      begin
         Ada.Integer_Text_IO.Get (Line, Target, Last);
         Ada.Float_Text_IO.Get (Line (Last + 1 .. Line'Last), X, Last);
         Ada.Float_Text_IO.Get (Line (Last + 1 .. Line'Last), Y, Last);
      end;
      R := (Target => Target, Pos => (X, Y));
      Available := True;
   end Read;

end Sensor_Input;

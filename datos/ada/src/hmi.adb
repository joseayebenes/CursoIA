with Ada.Text_IO; use Ada.Text_IO;

package body HMI is

   Active : array (Track_Id) of Boolean := (others => False);

   --  Req: SRS-0040
   procedure Show_Track (T : Track) is
   begin
      Put_Line ("TRACK" & Track_Id'Image (T.Id)
                & Float'Image (T.Pos.X) & Float'Image (T.Pos.Y));
   end Show_Track;

   --  Req: SRS-0044
   procedure Remove_Track (Id : Track_Id) is
   begin
      Put_Line ("TRACK_DELETED" & Track_Id'Image (Id));
   end Remove_Track;

   --  Req: SRS-0007, SRS-0041
   procedure Show_Alarm (Id : Track_Id; Text : String) is
   begin
      Active (Id) := True;
      Put_Line ("ALARM" & Track_Id'Image (Id) & " " & Text);
   end Show_Alarm;

   --  Req: SRS-0010
   procedure Acknowledge (Id : Track_Id) is
   begin
      Active (Id) := False;
   end Acknowledge;

   function Alarm_Active (Id : Track_Id) return Boolean is (Active (Id));

end HMI;

with HMI;
with Logger;
with Zones;

package body Alarms is

   Inside : array (Track_Id) of Boolean := (others => False);
   --  Whether each track was inside a restricted zone at its last report.

   --  Req: SRS-0007, SRS-0009
   procedure Check (T : Track) is
      Now_Inside : constant Boolean := Zones.In_Restricted_Zone (T.Pos);
   begin
      if Now_Inside and not Inside (T.Id) then
         HMI.Show_Alarm (T.Id, "entered restricted zone");
         Logger.Log ("Alarm: track" & Track_Id'Image (T.Id)
                     & " entered restricted zone");
      end if;
      Inside (T.Id) := Now_Inside;
   end Check;

end Alarms;

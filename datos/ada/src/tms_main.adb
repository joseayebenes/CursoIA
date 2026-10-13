with Tracks; use Tracks;
with Alarms;
with Clocks;
with Logger;
with Sensor_Input;
with Track_Store;

--  Main loop: reads the sensor reports, keeps the track table, raises the
--  alarms and purges the stale tracks once per Purge_Period (SDD 4.4).
procedure Tms_Main is
   Report     : Sensor_Input.Report;
   Available  : Boolean;
   Id         : Track_Id;
   Found, Ok  : Boolean;
   Next_Purge : Seconds := Purge_Period;
begin
   Logger.Log ("TMS started");
   loop
      Sensor_Input.Read (Report, Available);
      exit when not Available;
      declare
         Now : constant Seconds := Clocks.Now;
      begin
         Track_Store.Find (Report.Target, Id, Found);
         if Found then
            Track_Store.Update (Id, Report.Pos, Now);
            Ok := True;
         else
            Track_Store.Create (Report.Target, Report.Pos, Now, Id, Ok);
         end if;
         if Ok then
            Alarms.Check (Track_Store.Get (Id));
         end if;
         if Now >= Next_Purge then
            Track_Store.Purge_Stale (Now);
            Next_Purge := Now + Purge_Period;
         end if;
      end;
   end loop;
   Logger.Log ("TMS stopped");
end Tms_Main;

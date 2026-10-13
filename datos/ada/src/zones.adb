package body Zones is

   type Rectangle is record
      X_Min, X_Max, Y_Min, Y_Max : Float;
   end record;

   Restricted : constant array (1 .. 2) of Rectangle :=
     ((X_Min => 1_000.0, X_Max => 2_000.0, Y_Min => -500.0, Y_Max => 500.0),
      (X_Min => -3_000.0, X_Max => -2_500.0, Y_Min => 0.0, Y_Max => 800.0));

   --  Req: SRS-0007
   function In_Restricted_Zone (P : Position) return Boolean is
   begin
      for R of Restricted loop
         if P.X in R.X_Min .. R.X_Max and then P.Y in R.Y_Min .. R.Y_Max then
            return True;
         end if;
      end loop;
      return False;
   end In_Restricted_Zone;

end Zones;

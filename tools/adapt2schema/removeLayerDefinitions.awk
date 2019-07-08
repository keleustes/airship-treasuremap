BEGIN { DROPLINE = 0 }

/^  layeringDefinition:/ {
   DROPLINE = 1
   next
}

/TODO/ {
   DROPLINE = 0;
   print $0;
   next
}

/^  name:/ {
   DROPLINE = 0;
   print $0;
   next
}

/^  storagePolicy:/ {
   DROPLINE = 0;
   print $0;
   next
}

{
   if (DROPLINE == 0) {
      print $0;
   }
}

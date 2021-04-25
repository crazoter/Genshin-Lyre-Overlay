using System;
using System.IO;
using System.Linq;
using Melanchall.DryWetMidi.Core;
using Melanchall.DryWetMidi.Interaction;

namespace Genshin_Lyre_Overlay
{
    class Program
    {
        public static void ConvertMidiToText(string midiFilePath, string textFilePath)
        {
            var midiFile = MidiFile.Read(midiFilePath);

            File.WriteAllLines(textFilePath, 
                // NotesManagingUtilities.GetNotes(midiFile).Select(n => $"{n.NoteNumber} {n.Time} {n.Length}"));
                NotesManagingUtilities.GetNotes(midiFile).Select(n => $"{n.NoteNumber} {n.Time}"));
        }

        static void Main(string[] args)
        {
            // Run using `dotnet run`
            if (args.Length > 0) {
                Console.WriteLine("Converting "+ args[0] +" to "+args[0]+".txt!");
                var currDir = System.AppDomain.CurrentDomain.BaseDirectory;
                ConvertMidiToText(currDir + args[0], currDir + args[0] + ".txt");
            } else {
                Console.WriteLine("Converting file.mid to output.midi.txt!");
                var currDir = System.AppDomain.CurrentDomain.BaseDirectory;
                ConvertMidiToText(currDir + "file.mid", currDir + "output.midi.txt");
            }
        }
    }
}

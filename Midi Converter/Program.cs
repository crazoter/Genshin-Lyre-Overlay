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
            Console.WriteLine("Hello World!");
            var currDir = System.AppDomain.CurrentDomain.BaseDirectory;
            ConvertMidiToText(currDir + "file.mid", currDir + "output.txtmidi");
        }
    }
}

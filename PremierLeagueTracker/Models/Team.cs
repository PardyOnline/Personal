using System.ComponentModel.DataAnnotations;

namespace PremierLeagueTracker.Models
{
    public class Team
    {
        [Key]
        public int Id { get; set; }
        public string Name { get; set; }
        public int Wins { get; set; }
        public int Losses { get; set; }
        public int Draws { get; set; }
    }
}

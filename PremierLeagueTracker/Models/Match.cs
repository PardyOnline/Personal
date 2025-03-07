using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace PremierLeagueTracker.Models
{
    public class Match
    {
        [Key]
        public int Id { get; set; }
        
        [ForeignKey("HomeTeam")]
        public int HomeTeamId { get; set; }
        public Team HomeTeam { get; set; }

        [ForeignKey("AwayTeam")]
        public int AwayTeamId { get; set; }
        public Team AwayTeam { get; set; }

        public int HomeScore { get; set; }
        public int AwayScore { get; set; }
        public DateTime MatchDate { get; set; }
    }
}

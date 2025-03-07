using Microsoft.EntityFrameworkCore;
using PremierLeagueTracker.Models;

namespace PremierLeagueTracker.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

        public DbSet<Team> Teams { get; set; }
        public DbSet<Match> Matches { get; set; }

        protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {
            if (!optionsBuilder.IsConfigured)
            {
                optionsBuilder.UseSqlite("Data Source=PremierLeagueDB.db");
            }
        }
    }
}

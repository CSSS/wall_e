library(shiny)
library(DBI)

con = dbConnect(RPostgres::Postgres(),
                dbname = Sys.getenv('WALL_E_DB_DBNAME'),
                host = 'db',
                port = 5432,
                user = Sys.getenv('WALL_E_DB_USER'),
                password = Sys.getenv('WALL_E_DB_PASSWORD'))

ui = fluidPage(
    titlePanel("CSSS Discord Leaderboard")
)

server = function(input, output, session) {
    
}

shinyApp(ui = ui, server = server)

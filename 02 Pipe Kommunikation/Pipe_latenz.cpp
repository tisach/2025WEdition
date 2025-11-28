#include <chrono>
#include <fstream>
#include <iostream>
#include <vector>

#include <unistd.h>      // pipe, fork, read, write, close
#include <sys/types.h>   // pid_t
#include <sys/wait.h>    // waitpid
#include <sys/stat.h>    // mkdir


int main(int argc, char* argv[])
{
    // -------- Parameter: Anzahl der Messwerte --------
    long iterations = 200000;     // Standard: 200k Messungen

    if (argc > 1) {
        try {
            iterations = std::stol(argv[1]);
        } catch (...) {
            std::cerr << "Ungueltiger Parameter, verwende Standard: "
                      << iterations << "\n";
        }
    }

    // Warmup: erste Messungen zum „Einpendeln“ des Systems
    long warmup = std::min(1000L, iterations / 10);

    // -------- Pipes anlegen --------
    int parent_to_child[2];
    int child_to_parent[2];

    if (pipe(parent_to_child) == -1) {
        perror("pipe parent_to_child");
        return 1;
    }
    if (pipe(child_to_parent) == -1) {
        perror("pipe child_to_parent");
        return 1;
    }

    // -------- fork: Parent / Child --------
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return 1;
    }

    const char ping = 'X';
    char buf;

    using clock = std::chrono::steady_clock;      // monotone Uhr!
    using ns    = std::chrono::nanoseconds;

    if (pid == 0) {
        // ==================== Kindprozess ====================
        close(parent_to_child[1]);   // Kind liest nur
        close(child_to_parent[0]);   // Kind schreibt nur

        long total = warmup + iterations;
        for (long i = 0; i < total; ++i) {
            ssize_t r = read(parent_to_child[0], &buf, 1);
            if (r != 1) {
                if (r < 0) perror("child read");
                break;
            }
            ssize_t w = write(child_to_parent[1], &buf, 1);
            if (w != 1) {
                if (w < 0) perror("child write");
                break;
            }
        }

        close(parent_to_child[0]);
        close(child_to_parent[1]);
        _exit(0);
    }

    // ==================== Elternprozess ====================
    close(parent_to_child[0]);   // Parent schreibt nur
    close(child_to_parent[1]);   // Parent liest nur

    // results/ anlegen (falls nicht vorhanden)
    mkdir("results", 0777);

    std::ofstream csv("results/pipe_latenz.csv");
    if (!csv) {
        std::cerr << "Konnte results/pipe_latenz.csv nicht oeffnen.\n";
        return 1;
    }
    csv << "latenz_ns\n";

    // -------- Warmup (ohne Zeitmessung) --------
    for (long i = 0; i < warmup; ++i) {
        if (write(parent_to_child[1], &ping, 1) != 1) {
            perror("warmup write");
            break;
        }
        if (read(child_to_parent[0], &buf, 1) != 1) {
            perror("warmup read");
            break;
        }
    }

    // -------- eigentliche Messung --------
    for (long i = 0; i < iterations; ++i) {
        auto t0 = clock::now();

        if (write(parent_to_child[1], &ping, 1) != 1) {
            perror("write");
            break;
        }
        if (read(child_to_parent[0], &buf, 1) != 1) {
            perror("read");
            break;
        }

        auto t1 = clock::now();

        ns diff = std::chrono::duration_cast<ns>(t1 - t0);

        // Sicherheit: nur positive/vernünftige Werte speichern
        if (diff.count() <= 0) {
            // überspringen, falls aus irgendeinem Grund 0 oder negativ
            continue;
        }

        double one_way_ns = diff.count() / 2.0;   // Round-Trip -> Einweg
        csv << one_way_ns << "\n";
    }

    csv.close();

    close(parent_to_child[1]);
    close(child_to_parent[0]);

    int status = 0;
    waitpid(pid, &status, 0);

    return 0;
}
